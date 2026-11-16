from drf_spectacular.generators import SchemaGenerator as SG

HTTP_METHODS = {'get', 'post', 'put', 'patch', 'delete', 'options', 'head'}


class SchemaGenerator(SG):

    def parse(self, request, public):
        result = super().parse(request, public)
        # iterate over a copy of the keys to safely modify the original dictionary
        for path in list(result.keys()):
            # process only keys that look like valid API paths (starting with '/')
            if not isinstance(path, str) or not path.startswith('/'):
                continue

            path_item = result.get(path)
            if not isinstance(path_item, dict):
                continue
            # find all keys that are HTTP methods
            verbs_present = [k for k in list(path_item.keys()) if k.lower() in HTTP_METHODS]
            # remove all methods except GET
            for verb in verbs_present:
                if verb.lower() != 'get':
                    path_item.pop(verb, None)
            # if no allowed HTTP methods remain, remove the entire path
            still_has_allowed = any(k.lower() in {'get'} for k in path_item.keys())
            if not still_has_allowed:
                result.pop(path, None)

        return result
