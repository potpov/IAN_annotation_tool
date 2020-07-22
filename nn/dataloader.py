from torch.utils.data.dataset import Dataset
import numpy as np
from torchvision import transforms
import albumentations as albu


class AlveolarDataloader(Dataset):

    def __init__(self, args, data):

        self.data = data

        self.indices = np.arange(self.data.shape[0])
        if args.shuffle:
            np.random.seed(40)
            np.random.shuffle(self.indices)

        self.data = self.data.astype(np.float32)

        self.data_len = self.indices.size
        self.transforms = albu.Resize(192, 96, always_apply=True)
        # self.transforms = albu.PadIfNeeded(192, 128, border_mode=0, value=1)
        self.replicate = 'AlbuNet' in args.model

    def __len__(self):
        return self.data_len

    def __getitem__(self, index):

        # augmentation and rescaling
        aug_dict = {"image": self.data[index]}
        augmented = self.transforms(**aug_dict)
        image = augmented["image"]

        image = transforms.ToTensor()(image)

        # albunet and deeplab require RGB images
        if self.replicate:
            image = image.repeat(3, 1, 1)
        return image

    def split_dataset(self, trainset_size, valset_size=None):
        """
        split the indexes between training set, testing set and validation set.
        if valset_size is set to None its indixes vector is returned empty
        :param trainset_size: percentage of the training set
        :param valset_size: percentage of the validation set
        :return: arrays of indexes for: test_set, validation_set, test_set
        """
        split_train = int(np.floor(trainset_size * self.data_len))
        if valset_size is not None:
            split_val = split_train + int(np.floor(valset_size * self.data_len))
        else:
            split_val = split_train

        return self.indices[:split_train], self.indices[split_train:split_val], self.indices[split_val:]
