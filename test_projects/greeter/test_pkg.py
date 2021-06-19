from chkpkg import Package

if __name__ == "__main__":
    with Package() as pkg:
        pkg.run_python_code('import greeter')

        code = 'import greeter; greeter.say_hi()'
        assert pkg.run_python_code(code) == 'hi!'

        outp = pkg.run_shell_code('greeter_cli hi')
        print(f'got output [{outp}]')
        assert  outp == 'hi!'

        # program returns 2 without arguments, and that is not a failure
        pkg.run_shell_code('greeter_cli', expected_return_code=2)



        # how to print unicode on windows?..
        # code = 'import greeter; greeter.say_privet()'
        # assert pkg.run_python_code(code).strip() == 'привет!'

    print("\nPackage is OK!")
