from setuptools import setup, find_packages

setup(
    name="nepse-cli",
    version="1.0.0",
    description="Meroshare IPO automation CLI for family members",
    author="MenaceXnadin",
    py_modules=["main", "nepse_cli"],
    install_requires=[
        "playwright>=1.40.0",
    ],
    entry_points={
        "console_scripts": [
            "nepse=nepse_cli:main",
        ],
    },
    python_requires=">=3.7",
)
