import binascii
from datetime import datetime
import logging
import time

import click

from bdr_tse.tse_connector import TseConnector


@click.group()
@click.pass_context
@click.option("--tse_path", required=True, help="Path where the TSE is mounted")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(ctx, tse_path, debug):
    ctx.obj = TseConnector(tse_path)
    if debug:
        logging.basicConfig(level=logging.DEBUG)


@click.command()
@click.pass_obj
def start(tse):
    response = tse.start()
    response["serial"] = response["serial"].hex()
    click.echo(response)


@click.command()
@click.pass_obj
@click.option("--admin_puk", required=True, type=click.STRING)
@click.option("--admin_pin", required=True, type=click.STRING)
@click.option("--time_admin_puk", required=True, type=click.STRING)
@click.option("--time_admin_pin", required=True, type=click.STRING)
def initialize_pin_values(tse, admin_puk, admin_pin, time_admin_puk, time_admin_pin):
    tse.initialize_pin_values(
        admin_puk=admin_puk.encode("ascii"),
        admin_pin=admin_pin.encode("ascii"),
        time_admin_puk=time_admin_puk.encode("ascii"),
        time_admin_pin=time_admin_pin.encode("ascii"),
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
@click.option("--pin", required=True, type=click.STRING)
def authenticate_user(tse: TseConnector, admin, time_admin, pin: str):
    if time_admin == admin:
        raise click.UsageError("Exactly one of admin and time_admin must be given")
    user_id = TseConnector.UserId.ADMIN if admin else TseConnector.UserId.TIME_ADMIN
    click.echo(tse.authenticate_user(user_id, pin.encode("ascii")))


@click.command()
@click.pass_obj
@click.option("--admin", is_flag=True, type=click.BOOL)
@click.option("--time_admin", is_flag=True, type=click.BOOL)
@click.option("--puk", required=True, type=click.STRING)
@click.option("--new_pin", required=True, type=click.STRING)
def unblock_user(tse: TseConnector, admin, time_admin, puk: str, new_pin):
    if time_admin == admin:
        raise click.UsageError("Exactly one of admin and time_admin must be given")
    user_id = TseConnector.UserId.ADMIN if admin else TseConnector.UserId.TIME_ADMIN

    click.echo(tse.unblock_user(user_id, puk.encode("ascii"), new_pin.encode("ascii")))


@click.command()
@click.pass_obj
@click.option("--admin", is_flag=True, type=click.BOOL)
@click.option("--time_admin", is_flag=True, type=click.BOOL)
def logout(tse: TseConnector, admin, time_admin):
    user_id = TseConnector.UserId.ADMIN if admin else TseConnector.UserId.TIME_ADMIN
    tse.logout(user_id)


@click.command()
@click.pass_obj
@click.option("--time", "time_", type=click.INT)
def update_time(tse: TseConnector, time_):
    if not time_:
        time_ = int(time.time())
    tse.update_time(time_)


@click.command()
@click.pass_obj
def initialize(tse: TseConnector):
    tse.initialize()


@click.command()
@click.pass_obj
def get_serial_number(tse: TseConnector):
    click.echo(tse.get_serial_number().hex())


@click.command()
@click.pass_obj
@click.option("--client_id", required=True, type=click.STRING)
@click.option("--process_data", required=True, type=click.STRING)
@click.option("--process_type", required=True, type=click.STRING)
def start_transaction(tse: TseConnector, client_id, process_data, process_type):
    response = tse.start_transaction(
        client_id=client_id,
        process_data=process_data.encode("ascii"),
        process_type=process_type,
    )
    response["signature_value"] = response["signature_value"].hex()
    response["serial_number"] = response["serial_number"].hex()
    response["log_time"] = datetime.fromtimestamp(response["log_time"]).isoformat()
    click.echo(response)


@click.command()
@click.pass_obj
@click.option("--client_id", required=True, type=click.STRING)
@click.option("--key_serial_number", required=True, type=click.STRING)
def map_ers_to_key(tse: TseConnector, client_id, key_serial_number):
    return tse.map_ers_to_key(
        client_id=client_id, key_serial_number=binascii.unhexlify(key_serial_number)
    )


cli.add_command(start)
cli.add_command(initialize_pin_values)
cli.add_command(factory_reset)
cli.add_command(get_pin_status)
cli.add_command(authenticate_user)
cli.add_command(unblock_user)
cli.add_command(logout)
cli.add_command(initialize)
cli.add_command(update_time)
cli.add_command(start_transaction)
cli.add_command(get_serial_number)
cli.add_command(map_ers_to_key)


if __name__ == "__main__":
    cli()
