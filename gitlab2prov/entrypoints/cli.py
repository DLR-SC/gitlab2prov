from functools import partial
from functools import update_wrapper
from functools import wraps
from typing import Iterator
from prov.model import ProvDocument

import click

from gitlab2prov import __version__
from gitlab2prov import bootstrap
from gitlab2prov.config import Config
from gitlab2prov.domain import commands
from gitlab2prov.log import create_logger
from gitlab2prov.prov import operations


def enable_logging(ctx: click.Context, _, enable: bool):
    """Callback that optionally enables logging."""
    if enable:
        create_logger()


def invoke_command_line_from_config(ctx: click.Context, _, filepath: str):
    """Callback that executes a gitlab2prov run from a config file."""
    if not filepath:
        return
    config = Config.read(filepath)
    ok, err = config.validate()
    if not ok:
        ctx.fail(f"Validation failed: {err}")
    context = ctx.command.make_context(ctx.command.name, args=config.parse(), parent=ctx)
    ctx.command.invoke(context)
    ctx.exit()


def validate_config(ctx: click.Context, _, filepath: str):
    """Callback that validates config file using gitlab2prov/config/schema.json."""
    if not filepath:
        return
    config = Config.read(filepath)
    ok, err = config.validate()
    if not ok:
        ctx.fail(f"Validation failed: {err}")
    click.echo("Validation successful, the following command would be executed:\n")
    click.echo(f"gitlab2prov {' '.join(config.parse())}")
    ctx.exit()


def processor(func, wrapped=None):
    """Decorator that turns a function into a processor.

    A processor is a function that takes a stream of values, applies an operation
    to each value and returns a new stream of values.
    A processor therefore transforms a stream of values into a new stream of values.
    """

    @wraps(wrapped or func)
    def new_func(*args, **kwargs):
        def processor(stream):
            return func(stream, *args, **kwargs)

        return processor

    return update_wrapper(new_func, func)


def generator(func):
    """Decorator that turns a function into a generator.

    A generator is a special case of a processor.
    A generator is a processor that doesn't apply any operation
    to the values but adds new values to the stream.
    """

    @partial(processor, wrapped=func)
    def new_func(stream, *args, **kwargs):
        yield from stream
        yield from func(*args, **kwargs)

    return update_wrapper(new_func, func)


@click.group(chain=True, invoke_without_command=False)
@click.version_option(version=__version__, prog_name="gitlab2prov")
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    expose_value=False,
    callback=enable_logging,
    help="Enable logging to 'gitlab2prov.log'.",
)
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    expose_value=False,
    callback=invoke_command_line_from_config,
    help="Read config from file.",
)
@click.option(
    "--validate",
    type=click.Path(exists=True, dir_okay=False),
    expose_value=False,
    callback=validate_config,
    help="Validate config file and exit.",
)
@click.pass_context
def gitlab_cli(ctx):
    """
    Extract provenance information from GitLab projects.
    """
    ctx.obj = bootstrap.bootstrap("gitlab")


@click.group(chain=True, invoke_without_command=False)
@click.version_option(version=__version__, prog_name="github2prov")
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    expose_value=False,
    callback=enable_logging,
    help="Enable logging to 'github2prov.log'.",
)
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    expose_value=False,
    callback=invoke_command_line_from_config,
    help="Read config from file.",
)
@click.option(
    "--validate",
    type=click.Path(exists=True, dir_okay=False),
    expose_value=False,
    callback=validate_config,
    help="Validate config file and exit.",
)
@click.pass_context
def github_cli(ctx):
    ctx.obj = bootstrap.bootstrap("github")


@github_cli.result_callback()
@gitlab_cli.result_callback()
def process_commands(processors, **kwargs):
    """Execute the chain of commands.

    This function is called after all subcommands have been chained together.
    It executes the chain of commands by piping the output of one command
    into the input of the next command. Subcommands can be processors that transform
    the stream of values or generators that add new values to the stream.
    """
    # Start with an empty iterable.
    stream = ()

    # Pipe it through all stream processors.
    for processor in processors:
        stream = processor(stream)

    # Evaluate the stream and throw away the items.
    for _ in stream:
        pass


@click.command()
@click.option(
    "-u", "--url", "urls", multiple=True, type=str, required=True, help="Project url[s]."
)
@click.option("-t", "--token", required=True, type=str, help="Gitlab API token.")
@click.pass_obj
@generator
def extract(bus, urls: list[str], token: str):
    """Extract provenance information for one or more gitlab projects.

    This command extracts provenance information from one or multiple gitlab projects.
    The extracted provenance is returned as a combined provenance graph.
    """
    document = None

    for url in urls:
        doc = bus.handle(commands.Fetch(url, token))
        doc = bus.handle(commands.Serialize(url))
        doc = bus.handle(commands.Transform(doc))
        if not document:
            document = doc
        document.update(doc)

    document.description = f"extracted from '{', '.join(urls)}'"
    yield document


@click.command()
@click.option(
    "-i",
    "--input",
    "filenames",
    default=["-"],
    multiple=True,
    type=click.Path(dir_okay=False),
    help="Provenance file path (specify '-' to read from <stdin>).",
)
@click.pass_obj
@generator
def read(bus, filenames: list[str]):
    """Read provenance information from file[s].

    This command reads one provenance graph from a file/stdin or
    multiple graphs from multiple files.
    """
    for filename in filenames:
        try:
            document = bus.handle(commands.Read(filename=filename))
            document.description = "'<stdin>'" if filename == "-" else f"'{filename}'"
            yield document
        except Exception as e:
            click.echo(f"Could not open '{filename}': {e}", err=True)


@click.command()
@click.option(
    "-f",
    "--format",
    "formats",
    multiple=True,
    default=["json"],
    type=click.Choice(operations.SERIALIZATION_FORMATS),
    help="Serialization format.",
)
@click.option(
    "-o",
    "--output",
    "destination",
    default="-",
    help="Output file path.",
)
@processor
@click.pass_obj
def write(bus, documents, formats, destination):
    """Write provenance information to file[s].

    This command saves one or multiple provenance documents to a file.

    The output file path can be specified using the '-o' option.
    The serialization format can be specified using the '-f' option.
    """
    documents = list(documents)

    for i, document in enumerate(documents, start=1):

        for fmt in formats:
            filename = f"{destination}{'-' + str(i) if len(documents) > 1 else ''}.{fmt}"
            try:
                bus.handle(commands.Write(document, filename, fmt))
            except Exception as exc:
                click.echo(f"Could not save {document.description}: {exc}", err=True)

            yield document


@click.command()
@click.option("--use-pseudonyms", is_flag=True, help="Use pseudonyms.")
@click.option("--remove-duplicates", is_flag=True, help="Remove duplicate statements.")
@click.option(
    "--merge-aliased-agents",
    type=click.Path(exists=True),
    default="",
    help="Merge aliased agents.",
)
@processor
@click.pass_obj
def transform(
    bus,
    documents: Iterator[ProvDocument],
    use_pseudonyms: bool = False,
    remove_duplicates: bool = False,
    merge_aliased_agents: str = "",
):
    """Apply a set of transformations to provenance documents.

    This command applies a set of transformations to one or multiple provenance documents.
    """
    for document in documents:
        transformed = bus.handle(
            commands.Transform(document, use_pseudonyms, remove_duplicates, merge_aliased_agents)
        )
        transformed.description = f"normalized {document.description}"
        yield transformed


@click.command()
@processor
@click.pass_obj
def combine(bus, documents: Iterator[ProvDocument]):
    """Combine one or more provenance documents.

    This command combines one or multiple provenance documents into a single document.
    """
    documents = list(documents)
    descriptions = [doc.description for doc in documents]

    try:
        document = bus.handle(commands.Combine(documents))
        document = bus.handle(commands.Transform(document))
        document.description = f"combination of {', '.join(descriptions)}"
        yield document

    except Exception as exc:
        click.echo(f"Could not combine {', '.join(descriptions)}: {exc}", err=True)


@click.command()
@click.option(
    "--coarse",
    "resolution",
    flag_value="coarse",
    default=True,
    help="Print the number of PROV elements for each element type.",
)
@click.option(
    "--fine",
    "resolution",
    flag_value="fine",
    help="Print the number of PROV elements for each element type and each relation type.",
)
@click.option("--format", type=click.Choice(["csv", "table"]), default="table")
@click.option(
    "--verbose",
    is_flag=True,
    help="Print a textual summary of all operations applied to the graphs.",
)
@processor
@click.pass_obj
def statistics(
    bus, documents: Iterator[ProvDocument], resolution: str, format: str, verbose: bool
):
    """Print statistics for one or more provenance documents.

    This command prints statistics for each processed provenance graph.
    Statistics include the number of elements for each element type aswell as the number of relations for each relation type.
    Optionally, a short textual summary of all operations applied to the processed graphs can be printed to stdout.
    """
    for document in documents:
        try:
            statistics = bus.handle(commands.Statistics(document, resolution, format))
            if verbose:
                statistics = f"{document.description}\n\n{statistics}"
                click.echo(statistics)
        except Exception:
            click.echo("Could not compute statistics for {document.description}.", err=True)
        yield document


# CLI group for gitlab commands
gitlab_cli.add_command(extract)
gitlab_cli.add_command(read)
gitlab_cli.add_command(write)
gitlab_cli.add_command(combine)
gitlab_cli.add_command(transform)
gitlab_cli.add_command(statistics)

# CLI group for github commands
github_cli.add_command(extract)
github_cli.add_command(read)
github_cli.add_command(write)
github_cli.add_command(combine)
github_cli.add_command(transform)
github_cli.add_command(statistics)
