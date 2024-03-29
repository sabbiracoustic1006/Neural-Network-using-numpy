# -*- coding: utf-8 -*-
"""neural_net.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1CifWI2fWX0SKFfMuUXRpPLeesRS_SCNM
"""

import numpy as np
from sklearn import datasets
import math
from sklearn.model_selection import train_test_split
from tqdm import tqdm

class Dataset:
  def __init__(self,ds):
    for key,val in ds.items():
      setattr(self,key,val)

iris = Dataset(datasets.load_iris())

class NeuralNet:
  def __init__(self,input_size=4,hidden_sizes=[4,3],activations=['relu','relu'],num_classes=3):
    self.mean = 0
    self.std = 1
    self.num_layers = len(hidden_sizes)
    self.hidden_sizes = hidden_sizes
    setattr(self,'input_size',input_size)
    for idx,(size,a) in enumerate(zip(hidden_sizes,activations),start=1):
      setattr(self,'layer_%d'%idx,{'w':np.random.rand(input_size,size),
                                   'b':np.random.rand(1,size),
                                   'activation':a,
                                   'num_neurons':size})
      input_size = size
      
    a = 'softmax' if num_classes > 2 else 'sigmoid'
    self.loss_type = 'cross-entropy' if num_classes > 2 else 'binary-cross-entropy'
    
    setattr(self,'output_layer',{'w':np.random.rand(input_size,num_classes),
                                 'b':np.random.rand(1,num_classes),
                                   'activation':a})
    
    
  def __repr__(self):
    st = ''
    for key,val in self.__dict__.items():
      if isinstance(val,dict) and 'w' in  val.keys(): 
        st += '%s ---> %d neurons ---> activation %s\n'%(key,val['w'].shape[1],val['activation'])
      
    return st
  
  
  @staticmethod
  def activation(x,type_):
    if type_ =='softmax': a = np.exp(x)/(np.exp(x).sum(1).reshape(-1,1)+1e-7)
    elif type_ == 'relu': a = np.max((np.zeros_like(x),x),axis=0)
    elif type_ == 'sigmoid': a = 1/(1+math.exp(-x))
    
    return a
    
  
  def lossFunc(self,y,y_hat):
    if self.loss_type == 'cross-entropy': loss = -y*np.log(y_hat+1e-7)
    return loss.sum(1).mean()
  
  @staticmethod
  def accuracy(y,y_hat):
    return (y.argmax(1)==y_hat.argmax(1)).sum()/len(y)
  
  def activation_grad(self,z,type_):
    
    if type_ =='softmax': grads = self.activation(z,type_)*(1-self.activation(z,type_))
    elif type_ == 'relu': grads = (z>0).astype('float')
    elif type_ == 'sigmoid': grads = self.activation(z,type_)*(1-self.activation(z,type_))
    
    return grads
  
  def fit(self,x_train,y_train,batch_size=5,epochs=10,l_r=0.01):
    
    self.trainnet()
    
    self.mean = x_train.mean(0).reshape(1,-1)
    self.std = np.sqrt(x_train.var(0)+1e-7).reshape(1,-1)
    
    self.lr = l_r
    slices = [slice(i,i+batch_size) for i in range(0,len(x_train),batch_size)]
    
    with TQDM() as pbar:
     
      for epoch in range(epochs):
        pbar.on_train_begin({'num_batches':len(slices),'num_epoch':epochs})
        pbar.on_epoch_begin(epoch)
        
        losses = []
        accuracies = []
        
        for slice_ in slices:
          pbar.on_batch_begin()
          
          x_batch,y_batch = x_train[slice_],y_train[slice_]
          y_hat = self.__call__(x_batch)
          
          grads = self.backprop(y_batch)

          self.update_parameters(grads)
          
          loss = self.lossFunc(y_batch,y_hat)
          acc = self.accuracy(y_batch,y_hat)
          
          losses.append(loss)
          accuracies.append(acc)
          
          pbar.on_batch_end(logs={'loss':loss,'accuracy':acc})
        
        pbar.on_epoch_end({'train_loss':sum(losses)/len(losses),'train_accuracy':sum(accuracies)/len(accuracies),'params_1':self.output_layer['w'].sum(),'p_2':self.layer_1['w'].sum()
                          })
      
        if epoch % 5 == 0 and epoch != 0:
          if self.lr >= 1e-5:
            self.lr /= 2
            
  def eval(self):
    self.train = False
    
  def trainnet(self):
    self.train = True
    
  def backprop(self,y):
    y_hat,m_out = self.param_dict['z'][-1],self.param_dict['m'][-1]
    
    grads = [(-y/(y_hat+1e-7))*self.activation_grad(m_out,'softmax')]
    
    layer = 'output_layer'
    for idx,m in enumerate(reversed(self.param_dict['m'][:-1])):
        
        l_p = getattr(self,layer)
        w,a = l_p['w'],l_p['activation']
        
        grad = np.matmul(grads[idx],w.transpose())*self.activation_grad(m,a)
        grads.append(np.clip(grad,-100,100))
        
        layer = 'layer_%d'%(self.num_layers - idx)
      
        
    return grads
  
  def normalize(self,x):
    return (x-self.mean)/self.std
  
  
  def update_parameters(self,grads):
    layer_names = ['layer_%d'%i for i in range(1,self.num_layers+1)]+['output_layer']
    for layer,grad,z in zip(layer_names,reversed(grads),self.param_dict['z'][:-1]):
      grad[np.isnan(grad)]=0
      params = getattr(self,layer)
      params['w'] -= self.lr*np.matmul(z.transpose(),grad)/z.shape[0]
      params['b'] -= self.lr*grad.mean(0)
      setattr(self,layer,params)
      
  
  
  def __call__(self,x):
    
    num_in = len(x)
    
    z = self.normalize(x)
    
    if self.train: self.param_dict = {'z':[],'m':[]}; self.param_dict['z'].append(z)
    
    for _,dic in self.__dict__.items():
      if isinstance(dic,dict) and 'w' in dic.keys():
        m = np.matmul(z,dic['w']) + dic['b']
        z = self.activation(m,dic['activation'])

        if self.train:
          self.param_dict['m'].append(m)
          self.param_dict['z'].append(z)
      
      
    return z

class Callback(object):
    """
    Abstract base class used to build new callbacks.
    """

    def __init__(self):
        pass

    def set_params(self, params):
        self.params = params

    def set_trainer(self, model):
        self.trainer = model

    def on_epoch_begin(self, epoch, logs=None):
        pass

    def on_epoch_end(self, epoch, logs=None):
        pass

    def on_batch_begin(self, batch, logs=None):
        pass

    def on_batch_end(self, batch, logs=None):
        pass

    def on_train_begin(self, logs=None):
        pass

    def on_train_end(self, logs=None):
        pass


class TQDM(Callback):

    def __init__(self):
        """
        TQDM Progress Bar callback

        This callback is automatically applied to 
        every SuperModule if verbose > 0
        """
        self.progbar = None
        super(TQDM, self).__init__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # make sure the dbconnection gets closed
        if self.progbar is not None:
            self.progbar.close()

    def on_train_begin(self, logs):
        self.train_logs = logs

    def on_epoch_begin(self, epoch):
        try:
            self.progbar = tqdm(total=self.train_logs['num_batches'],
                                unit=' batches')
            self.progbar.set_description('Epoch %i/%i' % 
                            (epoch+1, self.train_logs['num_epoch']))
        except:
            pass

    def on_epoch_end(self, logs=None):
        log_data = {key: '%.04f' % logs[key] for key in logs.keys()}
        self.progbar.set_postfix(log_data)
        self.progbar.update()
        self.progbar.close()

    def on_batch_begin(self):
        self.progbar.update(1)

    def on_batch_end(self, logs=None):
        log_data = {key: '%.04f' % logs[key] for key in logs.keys()}
        self.progbar.set_postfix(log_data)
        
def to_one_hot(x):
  cols = len(np.unique(x))
  rows = len(x)
  vec = np.zeros((rows,cols))
  for idx,d in enumerate(x):
    vec[idx,d] = 1
    
  return vec

if __name__ == '__main__':
  one_hot=to_one_hot(iris.target)
  x_train,x_test,y_train,y_test=train_test_split(iris.data,one_hot)
  
  nn = NeuralNet(hidden_sizes=[5,4],activations=['relu']*2)
  nn.fit(x_train,y_train,epochs=50,batch_size=10,l_r=0.001)







