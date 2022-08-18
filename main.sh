python3.8 -m venv python_env
source python_env/bin/activate

pip3 install --upgrade pip && pip3 install requests
pip3 install -r requirements.txt
pip3 install --upgrade --no-deps --force-reinstall git+https://github.com/Pycord-Development/pycord
git init
git remote add origin https://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@github.com/BotsDiscordd/PublicBot.git
git config user.email "izayikhan@gmail.com"
git config user.name "LightningYT_lol"
python3.8 main.py