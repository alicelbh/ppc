# ppc
PPC project, 3TC

To launch the simulation, you need to start by running the control.py script. It handles the creation of the main message queue and of the market. Then, to add a house, you need to run “house.py prod_speed cons_speed private_key policy” in the terminal. The private key has to be below 200 (simply a convention to avoid having to check the existence of too many queues when ending the simulation) and the policy has to be either “scrooge”, “normal” or “generous”. You can add more houses by running the same command using different startup arguments in other terminals. To end the simulation, you only need to click on the button.
