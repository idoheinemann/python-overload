from setuptools import setup

setup(
    name='overload-python',
    version='2.0.0',
    description='A Python implementation of the overload feature',
    license='Apache License 2.0',
    packages=['overload'],
    author='Ido Heinemann',
    author_email='idohaineman@gmail.com',
    keywords=['overload', 'overloading', 'polymorphism'],
    url='https://github.com/idoheinemann/python-overload',
    install_requires=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package

        'Intended Audience :: Developers',  # Define that your audience are developers

        'Programming Language :: Python :: 3',  # Specify which python versions that you want to support
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
