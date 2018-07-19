from setuptools import setup

setup(name="python-kubernetes-operator",
      version="0.1.1",
      description="Simple Framework for Making Kubernetes Operators",
      url="https://github.com/ClearScore/python-kubernetes-operator",
      author="David Dyball",
      author_email="david.dyball@clearscore.com",
      license="private",
      packages=["pykubeop"],
      install_requires=[
          "kubernetes"
      ],
      zip_safe=True,
      test_suite="nose.collector",
      tests_require=["nose", "mock"])
