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


	class MLA(nn.Module):
		def __init__(self, d_model=32, num_heads=4, num_latents=4, latent_dim=32):
			super().__init__()
			self.latents = nn.Parameter(torch.randn(num_latents, latent_dim))
			self.attn = nn.MultiheadAttention(
				embed_dim=d_model,
				num_heads=num_heads,
				batch_first=True
			)
			self.ff = nn.Sequential(
				nn.Linear(d_model, d_model),
				nn.GELU(),
				nn.Linear(d_model, d_model)
			)

		def forward(self, x):
			batch_size = x.size(0)
			latents = self.latents.unsqueeze(0).expand(batch_size, -1, -1)
			updated_latents, _ = self.attn(query=latents, key=x, value=x)
			updated_latents = updated_latents + self.ff(updated_latents)
			return updated_latents  # (batch_size, num_latents, d_model)

	class Model(nn.Module):
		def __init__(self, vocab_dim, d_model=34, num_classes=2, num_cls_tokens=4):
			super().__init__()
			self.d_model = d_model
			self.num_cls_tokens = num_cls_tokens

			self.token_embed = nn.Embedding(vocab_dim, d_model)
			self.pos_embed = nn.Embedding(512, d_model)

			self.compress = nn.Sequential(
				nn.Linear(512, 150),
				nn.GELU(), nn.AlphaDropout(0.05), nn.RMSNorm(150),
				nn.Linear(150, d_model)
			)

			te = nn.TransformerEncoderLayer(
				d_model=d_model,
				nhead=6,
				dim_feedforward=100,
				dropout=0.26,
				activation=nn.functional.gelu,
				batch_first=True
			)
			self.encoder = nn.TransformerEncoder(te, num_layers=6)

			self.mla = MLA(d_model=d_model, num_heads=4, num_latents=8, latent_dim=d_model)

			self.head = nn.Linear((num_cls_tokens + self.mla.latents.size(0)) * d_model, num_classes)

		def forward(self, x):
			batch_size, seq_len = x.shape	

			pos = torch.arange(512, device=x.device).unsqueeze(0).expand(batch_size, 512)

			# pad to 512
			x = nn.functional.pad(x, (0, 512 - seq_len))  # (batch, 512)

			# embeddings
			x = self.token_embed(x) + self.pos_embed(pos)  # (batch, 512, d_model)

			x = self.compress(x.transpose(1, 2)).transpose(1, 2)  # adapt if needed

			out = self.encoder(x)

			cls_embeddings = out[:, :self.num_cls_tokens, :].reshape(batch_size, -1)
			mla_embeddings = self.mla(out).reshape(batch_size, -1)

			features = torch.cat([cls_embeddings, mla_embeddings], dim=-1)
			logits = self.head(features)
			return logits

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
