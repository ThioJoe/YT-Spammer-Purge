import os
import importlib
import configparser
import subprocess
import shutil

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = '1' # Disable HuggingFace's SYMLINK warning.

#from transformers import AutoTokenizer, AutoModelForSequenceClassification
#import torch
#from torch import nn
#from huggingface_hub import hf_hub_download
AutoTokenizer = None
torch = None
nn = None
hf_hub_download = None

# Default config
if not os.path.exists("ai_config.ini"):
	with open("ai_config.ini", "w") as configfile:
		configfile.write("[config]\n")
		configfile.write("model_name = BossBoss2021/spam-detection-ai\n")
		configfile.write("tokenizer_name = gpt2\n")
		configfile.write("threshold = 0.7\n")
		configfile.write("[automation]\n")
		configfile.write("autodownload_dependencies = False\n")

def load_config():
	config = configparser.ConfigParser()
	config.read("ai_config.ini")
	return config

# What device to use for the model
def get_device():
	if torch is None:
		return "cpu"
	
	return torch.device("cuda" if torch.cuda.is_available() else "cpu")

def get_logs():
	if not os.path.exists("ai_lost.latest"):
		with open("ai_lost.latest", "w") as f:
			f.write("")
	return open("ai_lost.latest", "r").read()

CONFIG = load_config()

model_name = "BossBoss2021/spam-detection-ai"

# Import libraries only when needed to not add more stuff to the dependencies.
def attempt_import(module_name):
	try:
		return importlib.import_module(module_name)
	except ImportError:
		if CONFIG["automation"]["autodownload_dependencies"] == "True":
			try:
				print(f"Downloading {module_name}...")
				logfile = get_logs()
				subprocess.run(["pip", "install", module_name], check=True, stdout=subprocess.DEVNULL, stderr=logfile)
				logfile.close()
				return importlib.import_module(module_name)
			except BaseException as e:
				print(f"Error: {module_name} could not be installed. Please install it manually with `pip install {module_name}`\
{'(or follow the instructions at https://pytorch.org)' if module_name == 'torch' else ''}.")
				return None
		else:
			print(f"Error: {module_name} is not installed. Please install it manually with `pip install {module_name}.")
			return None

MODEL = None
tokenizer = None

# Load a model by downloading the model file and class definitions from HF (Huggingface)
def load_model():
	global MODEL, tokenizer
	if MODEL is not None and tokenizer is not None:
		return MODEL, tokenizer
	
	global torch, nn, hf_hub_download, AutoTokenizer
	torch = attempt_import("torch")
	nn = torch.nn
	huggingface_hub = attempt_import("huggingface_hub")
	hf_hub_download = huggingface_hub.hf_hub_download
	transformers = attempt_import("transformers")
	AutoTokenizer = transformers.AutoTokenizer


	class Model(nn.Module):
		def __init__(self, vocab_dim, d_model=34, num_classes=2, num_cls_tokens=4):
			...

		def forward(self, x):
			...

	# The MLA and Model class definitions above are only for autocompletion and linting.
	# Below this comment is the code snippet that downloads the up-to-date class definitions from HF,
	# as well as the model
	utils_path = hf_hub_download(
		repo_id="BossBoss2021/spam-detection-ai",
		filename="utils.py"
	)
	shutil.move(utils_path, os.path.abspath(os.path.curdir + "/utils.py"))
	_utils = importlib.import_module("utils")
	os.remove(os.path.abspath(os.path.curdir + "/utils.py"))
	# Override class definitions with up-to-date classes to avoid future size missmatches.
	MLA = _utils.MLA
	Model = _utils.Model

	model_path = hf_hub_download(
		repo_id="BossBoss2021/spam-detection-ai",
		filename="model.pth"
	)
	tokenizer = AutoTokenizer.from_pretrained("gpt2")
	tokenizer.pad_token = tokenizer.eos_token

	ai_model = Model(len(tokenizer))
	ai_model.load_state_dict(torch.load(model_path))
	os.remove(model_path)

	MODEL = ai_model.to(get_device()).eval()
	quantize_dynamic = torch.quantization.quantize_dynamic
	if get_device() == "cpu":
		MODEL = quantize_dynamic(MODEL, {torch.nn.Linear}, dtype=torch.qint8)
	else:
		MODEL = MODEL.to(dtype=torch.float16)
	return MODEL, tokenizer
