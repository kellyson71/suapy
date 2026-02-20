import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="suapy",
    version="1.0.0",
    author="Suapy Contributors",
    author_email="seu_email@example.com",
    description="Uma biblioteca Python incrível e em pt-BR focada na vida do aluno acessando a API do SUAP (IFRN).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seuusuario/suapy",
    packages=setuptools.find_packages(include=["suapy", "suapy.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
    ],
    python_requires='>=3.6',
    install_requires=[
        'requests>=2.25.0',
    ],
    extras_require={
        'pandas': ['pandas>=1.0.0'],
    }
)
