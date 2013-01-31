import os.path

import utils
import database
import errors


class BaseDiagnostic(object):
    """The base class for diagnostics.
    """
    name = NotImplemented
    def __init__(self, rawfile_id):
        self.rawfile_id = rawfile_id
        self._precheck()
        self.fn = utils.get_rawfile_from_id(rawfile_id)
        self.diagnostic = self._compute()

    def _compute(self):
        raise NotImplementedError("The compute method must be defined by " \
                                    "subclasses of BaseDiagnostic.")


class FloatDiagnostic(BaseDiagnostic):
    """The base class for floating-point valued diagnostics.
    """
    def _precheck(self):
        """Check if the rawfile already has a diagnostic of this type
            in the database. An exception is raised if the check fails.

            Inputs:
                None

            Outputs:
                None
        """
        db = database.Database()
        db.connect()

        select = db.select([db.raw_diagnostics.c.raw_diagnostic_id]).\
                    where((db.raw_diagnostics.c.type==self.name) & \
                            (db.raw_diagnostics.c.rawfile_id==self.rawfile_id))
        result = db.execute(select)
        rows = result.fetchall()
        result.close()
        db.close()
        if len(rows) > 1:
            raise errors.InconsistentDatabaseError("There should be no " \
                            "more than one diagnostic value of each type " \
                            "per candidate. There are %d '%s' diagnostic " \
                            "values for this rawfile (ID: %d)" % \
                            (len(rows), self.name, self.rawfile_id))
        elif len(rows) == 1:
            raise errors.DatabaseError("There is already a '%s' diagnostic " \
                            "value in the DB for this rawfile (ID: %d)" % \
                            (self.name, self.rawfile_id))


class PlotDiagnostic(BaseDiagnostic):
    """The base class for plot diagnostics.
    """
    def _precheck(self):
        """Check if the rawfile already has a diagnostic of this type
            in the database. An exception is raised if the check fails.

            Inputs:
                None

            Outputs:
                None
        """
        db = database.Database()
        db.connect()

        select = db.select([db.raw_diagnostic_plots.c.raw_diagnostic_plot_id]).\
                    where((db.raw_diagnostic_plots.c.plot_type==self.name) & \
                            (db.raw_diagnostic_plots.c.rawfile_id==self.rawfile_id))
        result = db.execute(select)
        rows = result.fetchall()
        result.close()
        db.close()
        if len(rows) > 1:
            raise errors.InconsistentDatabaseError("There should be no " \
                            "more than one diagnostic plot of each type " \
                            "per candidate. There are %d '%s' diagnostic " \
                            "plots for this rawfile (ID: %d)" % \
                            (len(rows), self.name, self.rawfile_id))
        elif len(rows) == 1:
            raise errors.DatabaseError("There is already a '%s' diagnostic " \
                            "plot in the DB for this rawfile (ID: %d)" % \
                            (self.name, self.rawfile_id))
