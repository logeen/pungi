import re
import sys
import inspect
from .string import humanize, pp
from .expectations import Expectation
from .any import Any


def add(*matchers):
    for matcher in matchers:
        Expectation.addMatcher(matcher)


class Base(object):

    def __init__(self, actual, *expectedArgs, **expectedKwArgs):
        self.actual = actual
        self.expectedArgs = expectedArgs
        self.expectedKwArgs = expectedKwArgs
        self.negated = NegativeMatcher(self)

    def matchesExpectation(self):
        return self.matches(*self.expectedArgs, **self.expectedKwArgs)

    def message(self):
        ''' Override this to provide failure message'''
        name = self.__class__.__name__
        return "{0} {1}".format(humanize(name),
                        pp(*self.expectedArgs, **self.expectedKwArgs))

    def matches(self):
        ''' Override this to verify assert'''
        pass


class NegativeMatcher(object):

    def __init__(self, assertion):
        self.assertion = assertion

    def matchesExpectation(self):
        return not self.assertion.matchesExpectation()

    def message(self):
        return "not {0}".format(self.assertion.message())


class ToBe(Base):

    def matches(self, expected):
        return type(self.actual) == type(expected) and self.actual == expected


class ToEqual(Base):

    def matches(self, expected):
        return(ToEqual.eq(self.actual, expected) and
                ToEqual.eq(expected, self.actual))

    @staticmethod
    def compare(actual, expected):
        return(actual == expected and
                (type(actual) == type(expected) or
                isinstance(actual, Any) or isinstance(expected, Any)))

    @staticmethod
    def eq(actual, expected):
        if(hasattr(expected, '__dict__') and not isinstance(expected, Any)):
            for name, value in expected.__dict__.items():
                try:
                    actualValue = getattr(actual, name)
                except:
                    return False
                if(not ToEqual.eq(actualValue, value)):
                    return False
        try:
            enum = enumerate(expected)
        except:
            return ToEqual.compare(actual, expected)
        for i, item in enum:
            try:
                value = expected[item]
                key = item
            except:
                value = item
                key = i
            try:
                actualValue = actual[key]
            except:
                return False
            if(ToBe(value).matches(expected)):
                if(not ToEqual.compare(actualValue, value)):
                    return False
            elif(not ToEqual.eq(actualValue, value)):
                return False
        return True


class ToBeNone(Base):

    def matches(self):
        return self.actual is None


class ToBeTruthy(Base):

    def matches(self):
        return True if self.actual else False


class ToBeFalsy(Base):

    def matches(self):
        return False if self.actual else True


class ToMatch(Base):

    def matches(self, expected):
        return re.match(expected, self.actual)


class ToContain(Base):

    def matches(self, expected):
        return expected in self.actual


class ToBeGreaterThan(Base):

    def matches(self, expected):
        return self.actual > expected


class ToBeLessThan(Base):

    def matches(self, expected):
        return self.actual < expected


class ToRaise(Base):

    def matches(self, expectedException=None, message=None):
        try:
            self.actual()
        except:
            ex_type, ex = sys.exc_info()[:2]
            if(message is None or ex.args[0] == message):
                if(expectedException is None):
                    return True
                if(inspect.isclass(expectedException)):
                    if(issubclass(ex_type, expectedException)):
                        return True
                elif((isinstance(ex, type(expectedException)) or
                        isinstance(expectedException, Any)) and
                        ToEqual(ex).matches(expectedException)):
                    return True


class ToHaveBeenCalled(Base):

    def matches(self, times=None):
        return self.actual.wasCalled(times=times)


class ToHaveBeenCalledWith(Base):

    def matches(self, *args, **kwargs):
        return self.actual.wasCalledWith(*args, **kwargs)

    def message(self):
        if self.actual.callCount:
            calls = []
            for i in range(0, self.actual.callCount):
                calls.append(pp(*self.actual.argsForCall(i),
                        **self.actual.kwargsForCall(i)))
            return "{0} but was called with {1}".format(Base.message(self),
                    "; ".join(calls))
        return "{0} but it was never called.".format(Base.message(self))


class ToHaveBeenCalledBefore(Base):

    def matches(self, method):
        return self.actual.wasCalledBefore(method)
