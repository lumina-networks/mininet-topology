from setuptools import setup


setup(
    zip_safe=True,
    name='mininet-topology',
    version='1.0',
    author='jcastro',
    author_email='jcastro@brocade.com',
    packages=[
        'docopt',
        'mntopo',
        'traffic'
    ],
    description='Mininet utility to create topologies based on YAML files',
    license='LICENSE',
    install_requires=[
        "scapy"
    ],
    entry_points={
        'console_scripts': [
            'mnyml = mntopo.shell:main',
            'mntest = mntopo.checkershell:main',
            'mnrecv = traffic.receive:main',
            'mnsend = traffic.send:main',
            'topodc = mntopo.topodatacenter:main',
            'topotb = mntopo.topotable:main'
        ]
    }

)
