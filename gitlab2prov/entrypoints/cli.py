import sys
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

    A processor is a function that takes a stream of values, applies an operation to each value and returns a new stream of values.
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
    A generator is a processor that doesn't apply any operation to the values but adds new values to the stream.
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
    It executes the chain of commands by piping the output of one command into the input of the next command.
    Subcommands can be processors that transform the stream of values or generators that add new values to the stream.
    """
    # Start with an empty iterable.
    stream = ()

    # Pipe it through all stream processors.
    for processor in processors:
        stream = processor(stream)

    # Evaluate the stream and throw away the items.
    for _ in stream:
        pass


@click.command("extract")
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
        doc = bus.handle(commands.Normalize(doc))
        if not document:
            document = doc
        document.update(doc)

    document.description = f"extracted from '{', '.join(urls)}'"
    yield document


@click.command("load", short_help="Load provenance files.")
@click.option(
    "-i",
    "--input",
    "sources",
    multiple=True,
    type=click.Path(dir_okay=False),
    help="Provenance file path (specify '-' to read from <stdin>).",
)
@click.pass_obj
@generator
def load(bus, sources: list[str]):
    """Load provenance information from a file.

    This command reads one provenance graph from a file or multiple graphs from multiple files.
    """
    for filepath in sources:
        try:
            filename = sys.stdin if filepath == "-" else filepath
            document = bus.handle(commands.File2Document(filename))
            document.description = "'<stdin>'" if filepath == "-" else f"'{filepath}'"
            yield document
        except Exception as e:
            click.echo(f"Could not open '{filepath}': {e}", err=True)


@click.command("save")
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
    # TODO: think of a better default
    help="Output file path.",
)
@processor
@click.pass_obj
def save(bus, documents, formats, destination):
    """Save one or multiple provenance documents to a file.

    This command saves one or multiple provenance documents to a file.

    The output file path can be specified using the '-o' option.
    The serialization format can be specified using the '-f' option.
    """
    documents = list(documents)
    
    for i, document in enumerate(documents, start=1):
        
        for fmt in formats:
            filename = f"{destination}{'-' + str(i) if len(documents) > 1 else ''}.{fmt}"
            try:
                bus.handle(commands.Document2File(document, filename, fmt))
            except Exception as exc:
                click.echo(f"Could not save {document.description}: {exc}", err=True)

            yield document


@click.command("pseudonymize")
@processor
@click.pass_obj
def pseudonymize(bus, documents: Iterator[ProvDocument]):
    """Pseudonymize a provenance document.

    This command pseudonymizes one or multiple provenance documents.

    Pseudonymization is done by hashing attributes that contain personal information.
    Pseudonymization only affects agents and their attributes.
    """
    for document in documents:

        try:
            document = bus.handle(commands.Normalize(document, use_pseudonyms=True))
            document.description = f"pseudonymized {document.description}"
            yield document

        except Exception as exc:
            click.echo(f"Could not pseudonymize {document.description}: {exc}", err=True)


@click.command("combine")
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
        document = bus.handle(commands.Normalize(document))
        document.description = f"combination of {', '.join(descriptions)}"
        yield document

    except Exception as exc:
        click.echo(f"Could not combine {', '.join(descriptions)}: {exc}", err=True)


@click.command("stats")
@click.option(
    "--coarse",
    "resolution",
    flag_value="coarse",
    default=True,
    help="Print the number of PROV elements aswell as the overall number of relations.",
)
@click.option(
    "--fine",
    "resolution",
    flag_value="fine",
    help="Print the number of PROV elements aswell as the number of PROV relations for each relation type.",
)
@click.option("--format", type=click.Choice(["csv", "table"]), default="table")
@click.option(
    "--explain",
    is_flag=True,
    help="Print a textual summary of all operations applied to the graphs.",
)
@processor
@click.pass_obj
def stats(bus, documents: Iterator[ProvDocument], resolution: str, format: str, explain: bool):
    """Print statistics such as node counts and relation counts.

    This command prints statistics for each processed provenance graph.
    Statistics include the number of elements for each element type aswell as the number of relations for each relation type.
    Optionally, a short textual summary of all operations applied to the processed graphs can be printed to stdout.
    """
    for document in documents:
        try:
            statistics = bus.handle(commands.Statistics(document, resolution, format))
            if explain:
                statistics = f"{document.description}\n\n{statistics}"
                click.echo(statistics)
        except:
            click.echo("Could not compute statistics for {document.description}.", err=True)
        yield document


@click.command()
@click.option(
    "--mapping",
    "path_to_agent_map",
    type=click.Path(exists=True, dir_okay=False),
    help="File path to duplicate agent mapping.",
)
@processor
@click.pass_obj
def merge_duplicated_agents(bus, documents: Iterator[ProvDocument], path_to_agent_map: str):
    """Merge duplicated agents based on a name to aliases mapping.

    This command solves the problem of duplicated agents that can occur when the same physical user
    uses different user names and emails for his git and gitlab account.
    Based on a mapping of names to aliases the duplicated agents can be merged.
    """
    for document in documents:
        document = bus.handle(commands.Normalize(document, agent_mapping=path_to_agent_map))
        document.description += f"merged double agents {document.description}"
        yield document


gitlab_cli.add_command(extract)
gitlab_cli.add_command(stats)
gitlab_cli.add_command(combine)
gitlab_cli.add_command(pseudonymize)
gitlab_cli.add_command(save)
gitlab_cli.add_command(load)
gitlab_cli.add_command(merge_duplicated_agents)

github_cli.add_command(extract)
github_cli.add_command(stats)
github_cli.add_command(combine)
github_cli.add_command(pseudonymize)
github_cli.add_command(save)
github_cli.add_command(load)
github_cli.add_command(merge_duplicated_agents)
