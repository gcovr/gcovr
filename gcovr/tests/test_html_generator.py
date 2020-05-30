import pytest
from ..html_generator import _make_short_sourcename


@pytest.mark.parametrize("outfile,source_filename", [('../gcovr', 'C:\\other_dir\\project\\source.c'),
                                                     ('..\\gcovr', 'C:\\other_dir\\project\\source.c'),
                                                     ('..\\gcovr', 'C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c'),
                                                     ('..\\gcovr\\result.html', 'C:\\other_dir\\project\\source.c'),
                                                     ('..\\gcovr\\result', 'C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c'),
                                                     ('C:\\gcovr', 'C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c'),
                                                     ('C:/gcovr', 'C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c'),
                                                     ('C:/gcovr_files', 'C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c')
                                                     ])
def test_windows__make_short_sourcename(outfile, source_filename):

    result = _make_short_sourcename(outfile, source_filename)

    assert result.find(':') < 0 or (result.find(':') == 1 and result.find('C:') == 0)

    assert len(result) < 256
