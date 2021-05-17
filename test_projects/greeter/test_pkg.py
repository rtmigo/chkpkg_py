from chkpkg import Package

if __name__ == "__main__":
    with Package() as pkg:
        pkg.run_python_code('import greeter')

        code = 'import greeter; greeter.say_hi()'
        assert pkg.run_python_code(code).strip() == 'hi!'

        # how to print unicode on windows?..
        # code = 'import greeter; greeter.say_privet()'
        # assert pkg.run_python_code(code).strip() == 'привет!'

    print("\nPackage is OK!")
