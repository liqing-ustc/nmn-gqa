from utils import *
import h5py
from torch.utils.data.dataloader import default_collate
from torch.utils.data import Dataset, DataLoader
from modify_program import *
import torch

class GQA(Dataset):
    def __init__(self, split):
        super(GQA, self).__init__()

        self.img_feat_file = None
        self.img_feat_info = json.load(open(img_feat_info_path))
        
        dataset = json.load(open(os.path.join(dataroot, "questions1.2/%s_questions.json"%split)))
        for k, v in dataset.items():
            v['qid'] = k
        dataset = list(dataset.values())
        update_program(dataset)

        for sample in dataset:
            sample['answer_id'] = answer2id[sample['answer'].lower()]
            
        self.dataset = dataset
        
        
    def __getitem__(self, index):
        entry = self.dataset[index]
        #img_feat = torch.randn((30, 512))
        img_id = entry['imageId']
        img_feat_id = self.img_feat_info[img_id]['index']
        # Be careful when using hdf5 and multiprocess.
        # We must open the file in '__getitem__', rather than '__init__'
        # See https://discuss.pytorch.org/t/dataloader-when-num-worker-0-there-is-bug/25643/16
        if self.img_feat_file is None:
            self.img_feat_file = h5py.File(img_feat_path, 'r')['features']
        img_feat = self.img_feat_file[img_feat_id]
        img_feat = torch.FloatTensor(img_feat)
        program = entry['semantic']
        answer = entry['answer_id']
        return img_feat, program, answer 
    
    def __len__(self):
        return len(self.dataset)


def GQA_collate(batch):
    batch = list(zip(*batch))
    img_feat_batch = default_collate(batch[0])
    answer_batch = default_collate(batch[2])
    program_batch = batch[1]
    return [img_feat_batch, program_batch, answer_batch]