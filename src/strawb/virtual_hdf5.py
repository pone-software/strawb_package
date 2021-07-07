import h5py


class VirtualHDF5:
    def __init__(self, file_name, file_name_list):
        self.file_name = file_name
        self.file_name_list = file_name_list

        obj_dict = self.get_obj_dict(file_name_list)
        layout = self.get_layout(obj_dict)
        self.create_virtual_file(layout, file_name_list)

    def __iter_group__(self, obj, obj_dict=None):
        if obj_dict is None:
            obj_dict = {}

        for i in obj.values():
            if isinstance(i, h5py.Group):
                self.__iter_group__(i, obj_dict)
            else:
                v_source = h5py.VirtualSource(path_or_dataset=i.file.filename,
                                              name=i.name,
                                              shape=i.shape,
                                              dtype=i.dtype)
                if i.name in obj_dict:
                    obj_dict[i.name]['VDataSets'].append(v_source)
                    obj_dict[i.name]['total_length'] += i.shape[0]
                else:
                    obj_dict.update({i.name: {'VDataSets': [v_source], 'total_length': i.shape[0]}})
        return obj_dict

    def get_obj_dict(self, file_name_list):
        obj_dict = {}
        for i in file_name_list:
            with h5py.File(i, 'r') as f:
                # for i in f.items():
                self.__iter_group__(f, obj_dict=obj_dict)

        return obj_dict

    @staticmethod
    def get_layout(obj_dict):
        layout = {}
        for key_i, obj_i in obj_dict.items():
            dtype = obj_i['VDataSets'][0].dtype
            if dtype == object:
                # str doesn't work here :/
                # dtype = h5py.string_dtype()  # special_dtype(vlen=str)
                # dtype = 'S256'
                continue

            layout_i = h5py.VirtualLayout(shape=(obj_i['total_length'], *obj_i['VDataSets'][0].shape[1:]),
                                          dtype=dtype)

            offset = 0
            for v_source in obj_i['VDataSets']:
                length = v_source.shape[0]
                layout_i[offset: offset + length] = v_source
                offset += length

            layout.update({key_i: layout_i})

        return layout

    def create_virtual_file(self, layout, file_name_list):
        with h5py.File(self.file_name, 'w', libver='latest') as f:
            f.attrs.update({'file_names': file_name_list})
            for key_i, layout_i in layout.items():
                f.require_group(key_i.rsplit('/', 1)[0])
                f.create_virtual_dataset(key_i, layout_i, fillvalue=0)
