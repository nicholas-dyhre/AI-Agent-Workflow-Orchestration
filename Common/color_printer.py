from typing import Literal, overload

from colorama import Fore, Back, Style, init, deinit

class ColorPrinter:
    def __init__(self):
        print("setup colorprinter")
        init(autoreset=True)

    def __exit__(self):
        deinit()

    def printer(self, color: str, message, end: str | None = "\n", flush: Literal[False] = False):
        print(color + message, end=end, flush=flush)

colorPrinter = ColorPrinter()
def error(message):
    colorPrinter.printer(Fore.RED, message)
def success(message):
    colorPrinter.printer(Fore.GREEN, message)
def info(message):
    colorPrinter.printer(Fore.YELLOW, message)
def wild(message):
    colorPrinter.printer(Fore.MAGENTA, message)
# @overload
def back_blue(message, end, flush):
    colorPrinter.printer(Back.BLUE, message, end=end, flush=flush)
# @overload
# def back_blue(message):
#     colorPrinter.printer(Back.BLUE, message)
def bright(message, end, flush):
    colorPrinter.printer(Style.BRIGHT, message, end=end, flush=flush)



