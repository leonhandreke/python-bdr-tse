import click

from bdr_tse.tse_connector import TseConnector


@click.group()
@click.pass_context
@click.option('--tse_path', help='Path where the TSE is mounted')
def cli(ctx, tse_path):
    ctx.obj = TseConnector(tse_path)

@click.command()
@click.pass_obj
def start(tse):
    click.echo(tse.start())

@click.command()
@click.pass_obj
def initialize_pin_values(admin_puk, admin_pin, time_admin_puk, time_admin_pin):
    tse.initialize_pin_values(
        admin_puk=

    )

cli.add_command(start)


if __name__ == '__main__':
    cli()