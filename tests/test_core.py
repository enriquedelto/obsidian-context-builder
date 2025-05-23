import unittest
from pathlib import Path
import sys

# Adjust the path to import from the parent directory (root of the repo)
sys.path.insert(0, str(Path(__file__).parent.parent))
from core import generate_hierarchical_tags

class TestCoreGenerateHierarchicalTags(unittest.TestCase):
    def test_none_input(self):
        self.assertEqual(generate_hierarchical_tags(None), [])

    def test_simple_path(self):
        self.assertEqual(generate_hierarchical_tags(Path("Dir/SubDir/Note.md")), ['Dir/SubDir', 'Dir'])

    def test_no_parent_dir(self):
        self.assertEqual(generate_hierarchical_tags(Path("Note.md")), [])

    def test_path_with_spaces_and_hyphens(self):
        self.assertEqual(
            generate_hierarchical_tags(Path("My Folder/My-Sub Folder/A Note.md")),
            ['My_Folder/My_Sub_Folder', 'My_Folder']
        )

    def test_path_with_dots_in_folder_names(self):
        self.assertEqual(
            generate_hierarchical_tags(Path("Folder.v1/Sub.Folder.v2/MyNote.md")),
            ['Folder_v1/Sub_Folder_v2', 'Folder_v1']
        )

    def test_single_level_path(self):
        self.assertEqual(generate_hierarchical_tags(Path("ProjectAlpha/Readme.md")), ['ProjectAlpha'])

    def test_path_is_just_current_dir_reference(self):
        self.assertEqual(generate_hierarchical_tags(Path("./Note.md")), [])

    def test_empty_string_path(self):
        # Path("").parent is Path(".") which should result in no tags
        self.assertEqual(generate_hierarchical_tags(Path("")), [])

if __name__ == '__main__':
    unittest.main()
