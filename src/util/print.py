from colorama import Style, Fore

def eprint(text: str):
    print(f"{Fore.RED}{Style.BRIGHT}error{Fore.WHITE}{Style.NORMAL}: {text}")