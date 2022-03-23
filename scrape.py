
import os
import glob

excluded_folders = [
    '.vscode',
    '.git',
    'build',
    'bin',
    'node_modules',
    'test',
    'venv',
    'css',
    'well-known',
    'im',
    'fonts'
    'env'
]

included_folders = [
    'src',
    'app',
]

allowed_file_extensions = [
    'py',
    'js',
    'html'
]

translation_file = open('i18n/en-us.json', 'r')


def main():

    for directory in included_folders:
        for root, dirs, files in os.walk(top=directory):
            path = root.split(os.sep)

            for file in files:
                file_extension = file.split('.')[1]
                if allowed_file_extensions.count(file_extension) <= 0:
                    continue

                print(file)

    return

    output = os.walk('src')

    for root, dirs, files in output:
        print({'root': root, 'directory': dirs, 'files': files})

    return
    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk("."):
        print({'root': root, 'directory': dirs, 'files': files})

        # path = root.split(os.sep)
        # print path
        # if excluded_folders.count(os.path.basename(root).lower()) > 0:
        #     continue
        print(os.path.basename(root))
        # print((len(path) - 1) * '---', os.path.basename(root))
        for file in files:
            continue
            print(len(path) * '---', file)


if __name__ == '__main__':
    main()
