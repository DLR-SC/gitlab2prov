from functools import partial
from functools import update_wrapper
from functools import wraps

import click

from gitlab2prov import __version__
from gitlab2prov import bootstrap
from gitlab2prov.config import ConfigParser
from gitlab2prov.domain import commands
from gitlab2prov.log import create_logger
from gitlab2prov.prov import operations


def enable_logging(ctx: click.Context, _, enable: bool):
    """Callback that optionally enables logging."""
    if enable:
        create_logger()


def invoke_from_config(ctx: click.Context, _, filepath: str):
    """Callback that executes a gitlab2prov run from a config file."""
    if filepath:
        args = ConfigParser().parse(filepath)
        context = cli.make_context(f"{cli}", args=args, parent=ctx)
        cli.invoke(context)
        ctx.exit()


def validate_config(ctx: click.Context, _, filepath: str):
    """Callback that validates config file using gitlab2prov/config/schema.json."""
    if filepath:
        ok, err = ConfigParser().validate(filepath)
        if ok:
            config = ConfigParser().parse(filepath)
            click.echo("Validation successful, the following command would be executed:\n")
            click.echo(f"gitlab2prov {' '.join(config)}")
        else:
            ctx.fail(f"Validation failed: {err}")
        ctx.exit()


def processor(func, wrapped=None):
    """Helper decorator to rewrite a function so that it returns another
    function from it.
    """

    @wraps(wrapped or func)
    def new_func(*args, **kwargs):
        def processor(stream):
            return func(stream, *args, **kwargs)

        return processor

    return update_wrapper(new_func, func)


def generator(func):
    """Similar to the :func:`processor` but passes through old values
    unchanged and does not pass through the values as parameter."""

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
    is_eager=True,
    default=False,
    expose_value=False,
    callback=enable_logging,
    help="Enable logging to 'gitlab2prov.log'.",
)
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    expose_value=False,
    callback=invoke_from_config,
    help="Read config from file.",
)
@click.option(
    "--validate",
    is_eager=True,
    type=click.Path(exists=True, dir_okay=False),
    expose_value=False,
    callback=validate_config,
    help="Validate config file and exit.",
)
@click.pass_context
def cli(ctx):
    """
    Extract provenance information from GitLab projects.
    """
    ctx.obj = bootstrap.bootstrap()


@cli.result_callback()
def process_commands(processors, **kwargs):
    """This result callback is invoked with an iterable of all the chained
    subcommands.  As each subcommand returns a function
    we can chain them together to feed one into the other, similar to how
    a pipe on unix works.
    """
    # Start with an empty iterable.
    stream = ()

    # Pipe it through all stream processors.
    for processor in processors:
        stream = processor(stream)

    # Evaluate the stream and throw away the items.
    for _ in stream:
        pass


@cli.command("extract")
@click.option(
    "-u", "--url", "urls", multiple=True, type=str, required=True, help="Project url[s]."
)
@click.option("-t", "--token", required=True, type=str, help="Gitlab API token.")
@click.pass_obj
@generator
def do_extract(bus, urls: list[str], token: str):
    """Extract provenance information for one or more gitlab projects.

    This command extracts provenance information from one or multiple gitlab projects.
    The extracted provenance is returned as a combined provenance graph.
    """
    for url in urls:
        bus.handle(commands.Fetch(url, token))

    graph = bus.handle(commands.Serialize())
    graph.description = f"graph extracted from '{', '.join(urls)}'"
    yield graph

    bus.handle(commands.Reset())


@cli.command("load", short_help="Load provenance files.")
@click.option(
    "-i",
    "--input",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Provenance file path (specify '-' to read from <stdin>).",
)
@generator
def load(input):
    """Load provenance information from a file.

    This command reads one provenance graph from a file or multiple graphs from multiple files.
    """
    for filepath in input:
        try:
            if filepath == "-":
                graph = operations.deserialize_graph()
                graph.description = f"'<stdin>'"
                yield graph
            else:
                graph = operations.deserialize_graph(filepath)
                graph.description = f"'{filepath}'"
                yield graph
        except Exception as e:
            click.echo(f"Could not open '{filepath}': {e}", err=True)


@cli.command("save")
@click.option(
    "-f",
    "--format",
    multiple=True,
    default=["json"],
    type=click.Choice(operations.SERIALIZATION_FORMATS),
    help="Serialization format.",
)
@click.option(
    "-o",
    "--output",
    default="gitlab2prov-graph-{:04}",
    help="Output file path.",
)
@processor
def save(graphs, format, output):
    """Save provenance information to a file.

    This command writes each provenance graph that is piped to it to a file.
    """
    for idx, graph in enumerate(graphs, start=1):
        for fmt in format:
            try:
                serialized = operations.serialize_graph(graph, fmt)
                if output == "-":
                    click.echo(serialized)
                else:
                    with open(f"{output.format(idx)}.{fmt}", "w") as out:
                        click.echo(serialized, file=out)
            except Exception as e:
                click.echo(f"Could not save {graph.description}: {e}", err=True)
        yield graph


@cli.command("pseudonymize")
@processor
def pseudonymize(graphs):
    """Pseudonymize a provenance graph.

    This command pseudonymizes each provenance graph that is piped to it.
    """
    for graph in graphs:
        try:
            pseud = operations.pseudonymize(graph)
            pseud.description = f"pseudonymized {graph.description}"
            yield pseud
        except Exception as e:
            click.echo(f"Could not pseudonymize {graph.description}: {e}", err=True)


@cli.command("combine")
@processor
def combine(graphs):
    """Combine multiple graphs into one.

    This command combines all graphs that are piped to it into one.
    """
    graphs = list(graphs)
    try:
        combined = operations.combine(iter(graphs))
        descriptions = ", ".join(graph.description for graph in graphs)
        combined.description = f"combination of {descriptions}"
        yield combined
    except Exception as e:
        descriptions = "with ".join(graph.description for graph in graphs)
        click.echo(f"Could not combine {descriptions}: {e}", err=True)


@cli.command("stats")
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
@click.option(
    "--explain",
    "show_description",
    is_flag=True,
    help="Print a textual summary of all operations applied to the graphs.",
)
@click.option("--formatter", type=click.Choice(["csv", "table"]), default="table")
@processor
def stats(graphs, resolution, show_description, formatter):
    """Print statistics such as node counts and relation counts.

    This command prints statistics for each processed provenance graph.
    Statistics include the number of elements for each element type aswell as the number of relations for each relation type.
    Optionally, a short textual summary of all operations applied to the processed graphs can be printed to stdout.
    """
    for graph in graphs:
        try:
            if show_description:
                click.echo(f"\nDescription: {graph.description.capitalize()}\n")
            click.echo(
                operations.stats(
                    graph,
                    resolution,
                    formatter=operations.format_stats_as_ascii_table
                    if formatter == "table"
                    else operations.format_stats_as_csv,
                )
            )
            yield graph
        except Exception as e:
            click.echo(f"Could not display stats for {graph.description}: {e}", err=True)


@cli.command()
@click.option(
    "--mapping",
    type=click.Path(exists=True, dir_okay=False),
    help="File path to duplicate agent mapping.",
)
@processor
def merge_duplicated_agents(graphs, mapping):
    """Merge duplicated agents based on a name to aliases mapping.

    This command solves the problem of duplicated agents that can occur when the same physical user
    uses different user names and emails for his git and gitlab account.
    Based on a mapping of names to aliases the duplicated agents can be merged.
    """
    for graph in graphs:
        graph = operations.merge_duplicated_agents(graph, mapping)
        graph.description += f"merged double agents {graph.description}"
        yield graph
