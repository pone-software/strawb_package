import h5py


class VirtualHDF5:
    def __init__(self, file_name, file_name_list, obj_dict_filter=None):
        """Creates a virtual hdf5 file. A virtual hdf5 file can link data from multiple hdf5 files to one file.
        It also supports datasets, and a dataset in a virtual hdf5 file can be composed from
        different hdf5 datasets.

        PARAMETER
        ---------
        file_name: str,
            filename for the virtual hdf5 file.
        file_name_list: list[str]
            a list of hdf5 filenames which are the source of the virtual hdf5 file
        obj_dict_filter: dict, optional
            a filter class to detect invalid files from file_name_list.
            The class must have a 'filter' function which takes the 'obj_dict' and returns the modified obj_dict.
            i.e. obj_dict_filter.filter(obj_dict)

        EXAMPLE
        -------

        """
        self.file_name = file_name
        self.file_name_list = file_name_list
        self.obj_dict_filter = obj_dict_filter

        self.obj_dict = self.get_obj_dict()
        self.obj_dict = self.add_layout()
        self.create_virtual_file()

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

    @staticmethod
    def groups_from_obj_dict(obj_dict):
        return [i for i, item in obj_dict.items() if 'VDataSets' not in item]

    @staticmethod
    def datasets_from_obj_dict(obj_dict):
        return [i for i, item in obj_dict.items() if 'VDataSets' in item]

    def get_obj_dict(self, file_name_list=None):
        """Generates the obj_dict for the given files. The dictionary has the path as key and each value is another
        dictionary, i.e. obj_dict[key_i] = {..}, which holds information about the path. There are two types:
        Group (hdf5 directory): '/path/to/group': {'attrs': <group attrs>}
        DataSet               : '/path/to/dataset': {'attrs': <group attrs>,
                                                     'VDataSets': [VirtualSource0],
                                                     'total_length': <int>}
        If multiple files have a dataset with the identical </path/to/dataset>, 'VDataSets': [VirtualSource0, ...] holds
        the links to the dataset in the different files and the 'total_length' of all dataset along axis0 is calculated.

        The obj_dict looks like:
        {'/': {'attrs': {'dev_code': 'DEVICE001'}},
         '/group0': {'attrs': {'sensor_code': 1234}},
         '/group0/dataset0': {'VDataSets': [ < h5py._hl.vds.VirtualSource at 0x7fbb26959410 >,  # dataset file1
                                             < h5py._hl.vds.VirtualSource at 0x7fbb26972510 >],  # dataset file2
                              'total_length': 100,
                              'attrs': {'unit': 'ms'}
                             },
        '/group1': {'attrs': {}},
        ...
        }"""
        if file_name_list is not None:  # file_name_list can be updated later
            self.file_name_list = file_name_list

        obj_dict = {}
        for i, file_i in enumerate(self.file_name_list):
            try:
                with h5py.File(file_i, 'r', libver='latest', swmr=True) as f:
                    # for i in f.items():
                    self.__iter_group__(f, obj_dict=obj_dict, file_index=i)
            except OSError as err:
                print(f'Error at {file_i}: {err}')

        if self.obj_dict_filter is not None:
            obj_dict = self.obj_dict_filter.filter(obj_dict)

        return obj_dict

    def add_layout(self, obj_dict=None):
        """Adds the layout to each item of the obj_dict."""
        if obj_dict is not None:  # obj_dict can be updated later
            self.obj_dict = obj_dict

        # get only the datasets
        datasets = {i: self.obj_dict[i] for i in self.obj_dict if 'VDataSets' in self.obj_dict[i]}
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

            self.obj_dict[key_i].update({'layout': layout_i})

        return self.obj_dict

    def create_virtual_file(self, file_name=None, obj_dict=None):
        if file_name is not None:  # file name can be updated later
            self.file_name = file_name

        if obj_dict is not None:  # obj_dict can be updated later
            self.obj_dict = obj_dict

        with h5py.File(self.file_name, 'w', libver='latest') as f:
            f.attrs.update({'file_names': self.file_name_list})

            # create groups
            # get only the datasets
            groups = {i: self.obj_dict[i] for i in self.obj_dict if 'VDataSets' not in self.obj_dict[i]}
            for key_i, obj_i in groups.items():
                group = f.require_group(key_i)  # create the group in case, otherwise create dataset fails
                group.attrs.update(obj_i['attrs'])

            # create datasets
            # get only the datasets
            datasets = {i: self.obj_dict[i] for i in self.obj_dict if 'VDataSets' in self.obj_dict[i]}
            for key_i, obj_i in datasets.items():
                dataset = f.create_virtual_dataset(key_i, obj_i['layout'], fillvalue=0)
                dataset.attrs.update(obj_i['attrs'])


class DatasetsInGroupSameSize:
    """A Filter class which takes a obj_dict from VirtualHDF5 and checks if a group across all files have the same
    datasets and if the datasets in that group have the same shape along the first axis inside each file.
    In case it removes all datasets of the effected group for this file. In other words, a non consistent dataset in a
    group cause that all datasets of its group and for this file aren't added to the virtual HDF5 File. Other groups for
    the same file or the group for other files aren't effected."""
    @staticmethod
    def filter(obj_dict):
        hdf5_structure_dict = DatasetsInGroupSameSize.get_hdf5_structure(obj_dict)
        invalid_dict = DatasetsInGroupSameSize.get_invalid_groups(obj_dict, hdf5_structure_dict)
        obj_dict = DatasetsInGroupSameSize.pop_invalid_datasets(obj_dict, invalid_dict, hdf5_structure_dict)
        return obj_dict

    @staticmethod
    def get_hdf5_structure(obj_dict):
        datasets = [i for i, item in obj_dict.items() if 'VDataSets' in item]

        hdf5_structure_dict = {}
        for group, key in [[i.rsplit('/', 1)[0], i] for i in datasets]:
            if group in hdf5_structure_dict:
                hdf5_structure_dict[group].append(key)
            else:
                hdf5_structure_dict[group] = [key]
        return hdf5_structure_dict

    @staticmethod
    def get_invalid_groups(obj_dict, hdf5_structure_dict):
        invalid_dict = {}
        for group_i in hdf5_structure_dict:
            path_dict = {}

            for key_i in hdf5_structure_dict[group_i]:
                for j in obj_dict[key_i]['VDataSets']:
                    if j.path in path_dict:
                        path_dict[j.path].append(j.shape[0])
                    else:
                        path_dict[j.path] = [j.shape[0]]

            invalid_paths = set()
            for key_i, value_i in path_dict.items():
                if len(value_i) != len(hdf5_structure_dict[group_i]):
                    invalid_paths.update([key_i])
                    print(f'Not all datasets in group: "{group_i}"; file: "{key_i}"')
                elif len(set(value_i)) != 1:
                    invalid_paths.update([key_i])
                    print(f'More than one shape in group: "{group_i}"; file: "{key_i}"; shapes: {value_i}')

            if invalid_paths:
                invalid_dict[group_i] = invalid_paths

        return invalid_dict

    @staticmethod
    def pop_invalid_datasets(obj_dict, invalid_dict, hdf5_structure_dict):
        for group_i, files_i in invalid_dict.items():
            for dataset_j in hdf5_structure_dict[group_i]:
                j_pop = [j for j, set_j in enumerate(obj_dict[dataset_j]['VDataSets']) if set_j.path in files_i]

                j_pop.sort()  # sort the indexes
                for j in j_pop[::-1]:  # pop items from the end, otherwise indexes change
                    obj_j = obj_dict[dataset_j]['VDataSets'].pop(j)
                    obj_dict[dataset_j]['total_length'] -= obj_j.shape[0]
                    # print(dataset_j, obj_j.path, obj_j.shape[0])

        return obj_dict
