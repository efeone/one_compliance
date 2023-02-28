from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in one_compliance/__init__.py
from one_compliance import __version__ as version

setup(
	name="one_compliance",
	version=version,
	description="Frappe app to facilitate operations in Compliances and Tasks",
	author="efeone",
	author_email="info@efeone.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
