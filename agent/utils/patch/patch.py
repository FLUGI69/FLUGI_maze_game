def disableDistutilsWarning():
    import warnings

    warnings.filterwarnings(
        "ignore",
        message = "Setuptools is replacing distutils.",
        category = UserWarning,
        module = "_distutils_hack",
    )
