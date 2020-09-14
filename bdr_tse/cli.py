import logging
import time

import click

from bdr_tse.tse_connector import TseConnector

logging.basicConfig(level=logging.DEBUG)

@click.group()
@click.pass_context
@click.option("--tse_path", required=True, help='Path where the TSE is mounted')
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

@click.command()
@click.pass_obj
@click.option("--admin", is_flag=True, type=click.BOOL)
@click.option("--time_admin", is_flag=True, type=click.BOOL)
@click.option("--pin", type=click.STRING)
def authenticate_user(tse: TseConnector, admin, time_admin, pin: str):
    if time_admin == admin:
        raise click.UsageError("Exactly one of admin and time_admin must be given")
    user_id = TseConnector.UserId.ADMIN if admin else TseConnector.UserId.TIME_ADMIN
    click.echo(tse.authenticate_user(user_id, pin.encode("ascii")))

@click.command()
@click.pass_obj
@click.option("--time", "time_", type=click.INT)
def update_time(tse: TseConnector, time_):
    if not time_:
        time_ = int(time.time())
    tse.update_time(time_)


cli.add_command(start)
cli.add_command(initialize_pin_values)
cli.add_command(factory_reset)
cli.add_command(get_pin_status)
cli.add_command(authenticate_user)
cli.add_command(update_time)


if __name__ == '__main__':
    cli()