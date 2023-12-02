from setuptools import setup
import os


def get_requirements(requirements_file):
    """Get requirements from the requirements.txt"""
    dirname = os.path.dirname(os.path.realpath(__file__))
    requirements_file = os.path.join(dirname, requirements_file)
    with open(requirements_file, "r") as f:
        requirements = f.read().splitlines()
    return requirements


setup(
    name="Intecrate-CloudManager",
    version="1.0",
    description="Intecrate API Server",
    author="Kyle Tennison",
    python_requires=">=3.12",
    url="https://github.com/Intecrate/Intecrate-CloudManager",
    author_email="kyletennison05@gmail.com",
    packages=["cloud_manager"],
    install_requires=get_requirements("requirements.txt"),
)
