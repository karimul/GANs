
# coding: utf-8

# In[1]:


import torch
import torch.nn as nn
from torch.autograd import Variable
import torchvision.datasets as dset
import torchvision.transforms as transforms
import torch.nn.functional as F
import torch.optim as optim
import torchvision.utils as vutils
import sys
from utils.show_image import imshow
from torchvision import utils
from models import DCGAN_D,DCGAN_G


# In[3]:


z_size=128
hidden_size=64
batch_size = 128
dataset_name="LSUN"


# In[5]:


if dataset_name == 'MNIST':
    total_epoch=10000
    img_size=32
    image_chanel = 1
    model_name = 'WGAN_DC_MNIST'
    root = './data/mnist/'
    download = True
    trans = transforms.Compose([
        transforms.Scale(img_size),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    data_set = dset.MNIST(
        root=root, transform=trans, download=download)
if dataset_name == "LSUN":
    total_epoch=100000
    img_size=64
    image_chanel = 3
    model_name = 'WGAN_DC_LSUN'
    root = './data/lsun/'
    download = True
    trans = transforms.Compose([
        transforms.Scale(img_size),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])
    data_set = dset.LSUN(
        db_path=root, classes=['bedroom_train'], transform=trans)


# In[6]:


data_loader = torch.utils.data.DataLoader(
        dataset=data_set, batch_size=batch_size, shuffle=True)


# In[7]:


one = torch.FloatTensor([1])
noise_holder=torch.FloatTensor(batch_size, z_size, 1, 1)
input_holder = torch.FloatTensor(batch_size, 1, img_size, img_size)
if torch.cuda.is_available():
    one=one.cuda()
    noise_holder=noise_holder.cuda()
    input_holder=input_holder.cuda()
mone = one * -1


# In[8]:


def weights_init(m):
    classname = m.__class__.__name__
    if classname.find('Conv') != -1:
        m.weight.data.normal_(0.0, 0.02)
    elif classname.find('BatchNorm') != -1:
        m.weight.data.normal_(1.0, 0.02)
        m.bias.data.fill_(0)


# In[9]:


from tqdm import tqdm
G = DCGAN_G(isize=img_size, nz=z_size, nc=image_chanel, ngf=hidden_size, ngpu=0)
G.apply(weights_init)
D = DCGAN_D(isize=img_size, nz=z_size, nc=image_chanel, ndf=hidden_size, ngpu=0)
D.apply(weights_init)
print(G)
if torch.cuda.is_available():
    G.cuda()
    D.cuda()
G_lr = D_lr = 5e-5
optimizers = {
    'D': torch.optim.RMSprop(D.parameters(), lr=D_lr),
    'G': torch.optim.RMSprop(G.parameters(), lr=G_lr)
}
criterion = nn.BCELoss()
for epoch in tqdm(range(total_epoch)):
    for p in D.parameters():
        p.requires_grad = True
    if epoch<25 or epoch%500==0:
        iter_D=100
    else:
        iter_D=25
    for _ in range(iter_D):
        for p in D.parameters():
            p.data.clamp_(-0.01, 0.01)
        optimizers['D'].zero_grad()
        data=next(iter(data_loader))[0]
        if torch.cuda.is_available():
            data=data.cuda()
        input_holder.resize_as_(data).copy_(data)
        output_real = D(Variable(data))
        output_real.backward(one)
        noise_holder.resize_(data.size()[0], z_size, 1, 1).normal_(0, 1)
        noisev = Variable(noise_holder,volatile=True)
        fake_data = Variable(G(noisev).data)
        output_fake = D(fake_data)
        output_fake.backward(mone)
        optimizers['D'].step()

    for p in D.parameters():
        p.requires_grad = False
    optimizers['G'].zero_grad()
    noise_holder.resize_(data.size()[0], z_size, 1, 1).normal_(0, 1)
    noisev = Variable(noise_holder)
    fake_data = G(noisev)
    output_fake1 = D(fake_data)
    output_fake1.backward(one)
    optimizers['G'].step()

    if epoch % 1000 == 0:
        if torch.cuda.is_available():
            dd = utils.make_grid(fake_data.cpu().data[:64])
        else:
            dd = utils.make_grid(fake_data.data[:64])
        dd = dd.mul(0.5).add(0.5)
        vutils.save_image(dd, './results/%s_%d.png'%(model_name,epoch))

