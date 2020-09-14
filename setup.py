from setuptools import setup

setup(
    name="bdr_tse",
    version="0.1",
    py_modules=["bdr_tse"],
    install_requires=[
        "click",
        "construct",
    ],
    entry_points="""
        [console_scripts]
        bdr_tse=bdr_tse.cli:cli
    """,
)
