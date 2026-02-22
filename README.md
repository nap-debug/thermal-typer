# thermal-typer
Creates an interface with which to talk to a thermal receipt printer. Built for the Epson TM-T88V, but in theory can be modified to any receipt/label printer that uses ESC/POS.

## Using via SSH (cli.py)
1. ssh into the pi or machine running thermal-typer
2. cd ~/thermal-typer
3. python main.py
3. boom, you're in. shortcuts and commands provided upon startup. knock yourself out. 

## Using via browser (web.py)
1. open http://192.168.1.188:5000/
2. type something in the text box
3. hit print. 
4. boom, you did it. 