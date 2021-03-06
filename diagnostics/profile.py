import tempfile
import os
import shutil

import utils
import base

class ProfilePlotDiagnostic(base.PlotDiagnostic):
    name = 'Profile'
    description = "Fully scrunched profile."

    def _compute(self):
        utils.print_info("Creating profile plot for %s" % self.fn, 3)
        params = utils.prep_file(self.fn)
        handle, tmpfn = tempfile.mkstemp(suffix=".png")
        os.close(handle)
        cmd = ["psrplot", "-p", "flux", "-j", "TDFp", "-c", \
                "above:c=%s" % os.path.split(self.fn)[-1], \
                "-D", "%s/PNG" % tmpfn, self.fn]
        utils.execute(cmd)
        tmpdir = os.path.split(tmpfn)[0]
        pngfn = os.path.join(tmpdir, self.fn+".flux.png")
        shutil.move(tmpfn, pngfn) 
        return pngfn


Diagnostic = ProfilePlotDiagnostic

