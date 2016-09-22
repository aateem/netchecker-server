import setuptools


setuptools.setup(
    name='netchecker-server',
    version='0.1',
    summary='Network checker service to check connectivity in k8s cluster',
    author='Mirantis Inc.',
    license='Apache License, Version 2.0',
    packages=setuptools.find_packages(),
    install_requires=['flask', 'requests', 'waitress', 'six',
                      'wsgi-request-logger'],
    entry_points={
        'console_scripts': [
            'netchecker-server = netchecker_server.server:run'
        ]
    }
)
