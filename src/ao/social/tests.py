import doctest
import unittest


docfiles = ('middleware.rst', 'django.rst')


def test_suite():
    """Run all doctests in one test suite."""

    tests = [doctest.DocFileSuite(file,
        optionflags=doctest.ELLIPSIS) for file in docfiles]

    return unittest.TestSuite(tests)
