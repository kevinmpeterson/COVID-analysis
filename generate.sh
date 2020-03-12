if [ ! -d "./COVID-19" ]
then
	git clone https://github.com/CSSEGISandData/COVID-19.git
fi

cd COVID-19 && git pull
cd ..
python plot_cov.py
