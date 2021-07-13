import h5py


class VirtualHDF5:
    def __init__(self, file_name, file_name_list):
        self.file_name = file_name
        self.file_name_list = file_name_list

        obj_dict = self.get_obj_dict(file_name_list)
        obj_dict = self.add_layout(obj_dict)
        self.create_virtual_file(obj_dict, file_name_list)

    def __iter_group__(self, obj, obj_dict=None, file_index=0):
        if obj_dict is None:
            obj_dict = {}

        # get attrs of group
        if obj.name not in obj_dict:
            obj_dict.update({obj.name: {'attrs': dict(obj.attrs)}})
        else:
            self.__append_attrs__(obj=obj, obj_dict=obj_dict, file_index=file_index)

        # iter over items in group
        for i in obj.values():  # iterate over all items of the obj/group
            if isinstance(i, h5py.Group):  # if it is a group, iterate recursively
                self.__iter_group__(i, obj_dict=obj_dict, file_index=file_index)
            else:  # else, it is a dataset, append it.
                v_source = h5py.VirtualSource(path_or_dataset=i.file.filename,
                                              name=i.name,
                                              shape=i.shape,
                                              dtype=i.dtype)

                if i.name in obj_dict:
                    # noinspection PyUnresolvedReferences
                    obj_dict[i.name]['VDataSets'].append(v_source)
                    obj_dict[i.name]['total_length'] += i.shape[0]
                    self.__append_attrs__(obj=i, obj_dict=obj_dict, file_index=file_index)
                else:
                    obj_dict.update({i.name: {'VDataSets': [v_source],
                                              'total_length': i.shape[0],
                                              'attrs': dict(i.attrs)}
                                     })

        return obj_dict

    @staticmethod
    def __append_attrs__(obj, obj_dict, file_index):
        # get attrs of dataset
        for key_i, value_i in obj.attrs.items():
            if obj in obj_dict[obj.name]['attrs']:
                if obj_dict[obj.name]['attrs'][key_i] != value_i:
                    obj_dict[obj.name]['attrs'][f'{key_i}__{file_index}'] = value_i
            else:  # key_i isn't in attrs so far
                obj_dict[obj.name]['attrs'][key_i] = value_i
        return obj_dict

    def get_obj_dict(self, file_name_list):
        obj_dict = {}
        for i, file_i in enumerate(file_name_list):
            with h5py.File(file_i, 'r') as f:
                # for i in f.items():
                self.__iter_group__(f, obj_dict=obj_dict, file_index=i)
        return obj_dict

    @staticmethod
    def add_layout(obj_dict):
        """Adds the layout to each item of the obj_dict."""
        datasets = {i: obj_dict[i] for i in obj_dict if 'VDataSets' in obj_dict[i]}  # get only the datasets
        for key_i, obj_i in datasets.items():
            dtype = obj_i['VDataSets'][0].dtype
            if dtype == object:
                # str doesn't work here :/ - neither dtype = 'S256' nor h5py.string_dtype() nor special_dtype(vlen=str)
                continue

            # create layout
            layout_i = h5py.VirtualLayout(shape=(obj_i['total_length'], *obj_i['VDataSets'][0].shape[1:]), dtype=dtype)

            # add sources to layout
            offset = 0
            for v_source in obj_i['VDataSets']:
                length = v_source.shape[0]
                layout_i[offset: offset + length] = v_source
                offset += length

            obj_dict[key_i].update({'layout': layout_i})

        return obj_dict

    def create_virtual_file(self, obj_dict, file_name_list):
        with h5py.File(self.file_name, 'w', libver='latest') as f:
            f.attrs.update({'file_names': file_name_list})

            # create groups
            groups = {i: obj_dict[i] for i in obj_dict if 'VDataSets' not in obj_dict[i]}  # get only the datasets
            for key_i, obj_i in groups.items():
                group = f.require_group(key_i)  # create the group in case, otherwise create dataset fails
                group.attrs.update(obj_i['attrs'])

            # create datasets
            datasets = {i: obj_dict[i] for i in obj_dict if 'VDataSets' in obj_dict[i]}  # get only the datasets
            for key_i, obj_i in datasets.items():
                dataset = f.create_virtual_dataset(key_i, obj_i['layout'], fillvalue=0)
                dataset.attrs.update(obj_i['attrs'])
