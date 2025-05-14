from setuptools import setup, find_packages

setup(
    name="elephant-seals-counter",
    version="1.1.0",
    description="CLI to count elephant seals in aerial imagery",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Elephant Seals Team",
    url="https://github.com/brandonhjkim/elephant-seals-CLI",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "elephant_seals_cli": ["random_forest_mod1.joblib"]
    },
    install_requires=[
        "roboflow==1.1.56",
        "joblib==1.4.2",
        "numpy==2.2.3",
        "pandas==2.2.3",
        "pillow==11.1.0",
        "scikit-learn==1.6.1",
    ],
    entry_points={
        "console_scripts": [
            "seal-counter = elephant_seals_cli.seals_counter_cli:main",
        ],
    },
    python_requires=">=3.7",
)