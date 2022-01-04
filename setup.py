from setuptools import setup

setup(
    name="datamodels",
    version="0.1.0",
    author="David Katz",
    author_email="david@crossentropy.solution",
    packages=[
        "datamodels"
    ],
    description="Pokemon Rest App",
    long_description=open("README.md").read(),
    install_requires=open("requirements.txt").read().split("\n"),
)