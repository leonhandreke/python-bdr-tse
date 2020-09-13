import logging

import click

from bdr_tse.tse_connector import TseConnector

logging.basicConfig(level=logging.DEBUG)

@click.group()
@click.pass_context
@click.option("--tse_path", help='Path where the TSE is mounted')
def cli(ctx, tse_path):
    ctx.obj = TseConnector(tse_path)

@click.command()
@click.pass_obj
def start(tse):
    click.echo(tse.start())

@click.command()
@click.pass_obj
@click.option("--admin_puk", required=True, type=click.STRING)
@click.option("--admin_pin", required=True, type=click.STRING)
@click.option("--time_admin_puk", required=True, type=click.STRING)
@click.option("--time_admin_pin", required=True, type=click.STRING)
def initialize_pin_values(tse, admin_puk, admin_pin, time_admin_puk, time_admin_pin):
    tse.initialize_pin_values(
        admin_puk=admin_puk.encode('ascii'),
        admin_pin=admin_pin.encode('ascii'),
        time_admin_puk=time_admin_puk.encode('ascii'),
        time_admin_pin=time_admin_pin.encode('ascii'),
    )

@click.command()
@click.pass_obj
def factory_reset(tse):
    tse.factory_reset()

@click.command()
@click.pass_obj
def get_pin_status(tse):
    click.echo(tse.get_pin_status())


cli.add_command(start)
cli.add_command(initialize_pin_values)
cli.add_command(factory_reset)
cli.add_command(get_pin_status)


if __name__ == '__main__':
    cli()