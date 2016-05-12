from setuptools import setup, find_packages

version = '0.4.0'

long_description = """
JSON-RPC Parts is a library of composable components one would need to assemble a JSON-RPC server or client.

The parts provided are JSON-RPC message parser and serializer, a generic request handler collection, a WSGI-specific request handler and bits and pieces.

This JSON-RPC Parts collection supports both, JSON-RPC v.1.0 and v.2.0 including "batch" mode for v.2.0.

The parts are split into separate modules that can be used separately from this collection.

Since this collection is MIT-licensed, you are free grab a part of this code and use it in alsmost any.
"""

project_home = 'http://github.com/dvdotsenko/jsonrpc.py'


if __name__ == "__main__":
    setup(
        name='jsonrpcparts',
        description='JSON-RPC client and server components',
        long_description=long_description,
        version=version,
        author='Daniel Dotsenko',
        author_email='dotsa@hotmail.com',
        url=project_home,
        download_url=project_home+'/tarball/master',
        classifiers=[
            "Development Status :: 4 - Beta",
            "Environment :: Web Environment",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7",
            "Topic :: Internet",
            "Topic :: Internet :: WWW/HTTP",
            "Topic :: Internet :: WWW/HTTP :: WSGI",
            "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
        ],
        keywords = ['JSON', 'jsonrpc', 'rpc', 'wsgi'],
        license='MIT',
        packages=find_packages(),
        include_package_data=True,
        install_requires=['requests']
    )

# Next:
# python setup.py register
# python setup.py sdist upload
