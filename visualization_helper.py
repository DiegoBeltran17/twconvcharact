import matplotlib
import os
import time
from selenium import webdriver


def init_plot_style():
    matplotlib.style.use('seaborn-ticks')
    matplotlib.rcParams['font.size'] = 16
    matplotlib.rcParams['ytick.labelsize'] = 14
    matplotlib.rcParams['xtick.labelsize'] = 14
    matplotlib.rcParams['axes.labelsize'] = 16
    matplotlib.rcParams['axes.titlesize'] = 16
    matplotlib.rcParams['text.usetex'] = True

    # matplotlib.style.use('seaborn-ticks')
    # matplotlib.rcParams['font.size'] = 14
    # matplotlib.rcParams['ytick.labelsize'] = 14
    # matplotlib.rcParams['xtick.labelsize'] = 14
    # matplotlib.rcParams['axes.labelsize'] = 14
    # matplotlib.rcParams['axes.titlesize'] = 16


def export_map(m, relative_path_without_ext):
    delay=5
    fn=f'{relative_path_without_ext}.html'
    tmpurl='file://{path}/{mapfile}'.format(path=os.getcwd(),mapfile=fn)
    m.save(fn)

    browser = webdriver.Firefox()
    browser.get(tmpurl)
    #Give the map tiles some time to load
    time.sleep(delay)
    browser.save_screenshot(f'{relative_path_without_ext}.png')
    browser.quit()