package com.marvel.reader.`data`.db

import androidx.room.InvalidationTracker
import androidx.room.RoomOpenDelegate
import androidx.room.migration.AutoMigrationSpec
import androidx.room.migration.Migration
import androidx.room.util.TableInfo
import androidx.room.util.TableInfo.Companion.read
import androidx.room.util.dropFtsSyncTriggers
import androidx.sqlite.SQLiteConnection
import androidx.sqlite.execSQL
import javax.`annotation`.processing.Generated
import kotlin.Lazy
import kotlin.String
import kotlin.Suppress
import kotlin.collections.List
import kotlin.collections.Map
import kotlin.collections.MutableList
import kotlin.collections.MutableMap
import kotlin.collections.MutableSet
import kotlin.collections.Set
import kotlin.collections.mutableListOf
import kotlin.collections.mutableMapOf
import kotlin.collections.mutableSetOf
import kotlin.reflect.KClass

@Generated(value = ["androidx.room.RoomProcessor"])
@Suppress(names = ["UNCHECKED_CAST", "DEPRECATION", "REDUNDANT_PROJECTION", "REMOVAL"])
public class AppDatabase_Impl : AppDatabase() {
  private val _issueDao: Lazy<IssueDao> = lazy {
    IssueDao_Impl(this)
  }


  private val _progressDao: Lazy<ProgressDao> = lazy {
    ProgressDao_Impl(this)
  }


  private val _reportDao: Lazy<ReportDao> = lazy {
    ReportDao_Impl(this)
  }


  private val _settingDao: Lazy<SettingDao> = lazy {
    SettingDao_Impl(this)
  }


  protected override fun createOpenDelegate(): RoomOpenDelegate {
    val _openDelegate: RoomOpenDelegate = object : RoomOpenDelegate(1,
        "79b17e22c6cc9cf7f06a9cd761fbe329", "d7a0d2488dcc133accb519c478ad3c0b") {
      public override fun createAllTables(connection: SQLiteConnection) {
        connection.execSQL("CREATE TABLE IF NOT EXISTS `issues` (`orderNum` INTEGER NOT NULL, `title` TEXT NOT NULL, `issue` INTEGER NOT NULL, `phase` TEXT NOT NULL, `event` TEXT, `year` TEXT NOT NULL, `totalPages` INTEGER NOT NULL, `availablePages` INTEGER NOT NULL, `downloadedPages` INTEGER NOT NULL, PRIMARY KEY(`orderNum`))")
        connection.execSQL("CREATE TABLE IF NOT EXISTS `reading_progress` (`orderNum` INTEGER NOT NULL, `currentPage` INTEGER NOT NULL, `isRead` INTEGER NOT NULL, `updatedAt` TEXT NOT NULL, PRIMARY KEY(`orderNum`))")
        connection.execSQL("CREATE TABLE IF NOT EXISTS `reports` (`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `issueOrder` INTEGER NOT NULL, `pageNum` INTEGER, `reportType` TEXT NOT NULL, `description` TEXT NOT NULL, `resolved` INTEGER NOT NULL, `createdAt` TEXT NOT NULL)")
        connection.execSQL("CREATE TABLE IF NOT EXISTS `settings` (`key` TEXT NOT NULL, `value` TEXT NOT NULL, PRIMARY KEY(`key`))")
        connection.execSQL("CREATE TABLE IF NOT EXISTS room_master_table (id INTEGER PRIMARY KEY,identity_hash TEXT)")
        connection.execSQL("INSERT OR REPLACE INTO room_master_table (id,identity_hash) VALUES(42, '79b17e22c6cc9cf7f06a9cd761fbe329')")
      }

      public override fun dropAllTables(connection: SQLiteConnection) {
        connection.execSQL("DROP TABLE IF EXISTS `issues`")
        connection.execSQL("DROP TABLE IF EXISTS `reading_progress`")
        connection.execSQL("DROP TABLE IF EXISTS `reports`")
        connection.execSQL("DROP TABLE IF EXISTS `settings`")
      }

      public override fun onCreate(connection: SQLiteConnection) {
      }

      public override fun onOpen(connection: SQLiteConnection) {
        internalInitInvalidationTracker(connection)
      }

      public override fun onPreMigrate(connection: SQLiteConnection) {
        dropFtsSyncTriggers(connection)
      }

      public override fun onPostMigrate(connection: SQLiteConnection) {
      }

      public override fun onValidateSchema(connection: SQLiteConnection):
          RoomOpenDelegate.ValidationResult {
        val _columnsIssues: MutableMap<String, TableInfo.Column> = mutableMapOf()
        _columnsIssues.put("orderNum", TableInfo.Column("orderNum", "INTEGER", true, 1, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsIssues.put("title", TableInfo.Column("title", "TEXT", true, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsIssues.put("issue", TableInfo.Column("issue", "INTEGER", true, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsIssues.put("phase", TableInfo.Column("phase", "TEXT", true, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsIssues.put("event", TableInfo.Column("event", "TEXT", false, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsIssues.put("year", TableInfo.Column("year", "TEXT", true, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsIssues.put("totalPages", TableInfo.Column("totalPages", "INTEGER", true, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsIssues.put("availablePages", TableInfo.Column("availablePages", "INTEGER", true, 0,
            null, TableInfo.CREATED_FROM_ENTITY))
        _columnsIssues.put("downloadedPages", TableInfo.Column("downloadedPages", "INTEGER", true,
            0, null, TableInfo.CREATED_FROM_ENTITY))
        val _foreignKeysIssues: MutableSet<TableInfo.ForeignKey> = mutableSetOf()
        val _indicesIssues: MutableSet<TableInfo.Index> = mutableSetOf()
        val _infoIssues: TableInfo = TableInfo("issues", _columnsIssues, _foreignKeysIssues,
            _indicesIssues)
        val _existingIssues: TableInfo = read(connection, "issues")
        if (!_infoIssues.equals(_existingIssues)) {
          return RoomOpenDelegate.ValidationResult(false, """
              |issues(com.marvel.reader.data.db.IssueEntity).
              | Expected:
              |""".trimMargin() + _infoIssues + """
              |
              | Found:
              |""".trimMargin() + _existingIssues)
        }
        val _columnsReadingProgress: MutableMap<String, TableInfo.Column> = mutableMapOf()
        _columnsReadingProgress.put("orderNum", TableInfo.Column("orderNum", "INTEGER", true, 1,
            null, TableInfo.CREATED_FROM_ENTITY))
        _columnsReadingProgress.put("currentPage", TableInfo.Column("currentPage", "INTEGER", true,
            0, null, TableInfo.CREATED_FROM_ENTITY))
        _columnsReadingProgress.put("isRead", TableInfo.Column("isRead", "INTEGER", true, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsReadingProgress.put("updatedAt", TableInfo.Column("updatedAt", "TEXT", true, 0,
            null, TableInfo.CREATED_FROM_ENTITY))
        val _foreignKeysReadingProgress: MutableSet<TableInfo.ForeignKey> = mutableSetOf()
        val _indicesReadingProgress: MutableSet<TableInfo.Index> = mutableSetOf()
        val _infoReadingProgress: TableInfo = TableInfo("reading_progress", _columnsReadingProgress,
            _foreignKeysReadingProgress, _indicesReadingProgress)
        val _existingReadingProgress: TableInfo = read(connection, "reading_progress")
        if (!_infoReadingProgress.equals(_existingReadingProgress)) {
          return RoomOpenDelegate.ValidationResult(false, """
              |reading_progress(com.marvel.reader.data.db.ProgressEntity).
              | Expected:
              |""".trimMargin() + _infoReadingProgress + """
              |
              | Found:
              |""".trimMargin() + _existingReadingProgress)
        }
        val _columnsReports: MutableMap<String, TableInfo.Column> = mutableMapOf()
        _columnsReports.put("id", TableInfo.Column("id", "INTEGER", true, 1, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsReports.put("issueOrder", TableInfo.Column("issueOrder", "INTEGER", true, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsReports.put("pageNum", TableInfo.Column("pageNum", "INTEGER", false, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsReports.put("reportType", TableInfo.Column("reportType", "TEXT", true, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsReports.put("description", TableInfo.Column("description", "TEXT", true, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsReports.put("resolved", TableInfo.Column("resolved", "INTEGER", true, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsReports.put("createdAt", TableInfo.Column("createdAt", "TEXT", true, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        val _foreignKeysReports: MutableSet<TableInfo.ForeignKey> = mutableSetOf()
        val _indicesReports: MutableSet<TableInfo.Index> = mutableSetOf()
        val _infoReports: TableInfo = TableInfo("reports", _columnsReports, _foreignKeysReports,
            _indicesReports)
        val _existingReports: TableInfo = read(connection, "reports")
        if (!_infoReports.equals(_existingReports)) {
          return RoomOpenDelegate.ValidationResult(false, """
              |reports(com.marvel.reader.data.db.ReportEntity).
              | Expected:
              |""".trimMargin() + _infoReports + """
              |
              | Found:
              |""".trimMargin() + _existingReports)
        }
        val _columnsSettings: MutableMap<String, TableInfo.Column> = mutableMapOf()
        _columnsSettings.put("key", TableInfo.Column("key", "TEXT", true, 1, null,
            TableInfo.CREATED_FROM_ENTITY))
        _columnsSettings.put("value", TableInfo.Column("value", "TEXT", true, 0, null,
            TableInfo.CREATED_FROM_ENTITY))
        val _foreignKeysSettings: MutableSet<TableInfo.ForeignKey> = mutableSetOf()
        val _indicesSettings: MutableSet<TableInfo.Index> = mutableSetOf()
        val _infoSettings: TableInfo = TableInfo("settings", _columnsSettings, _foreignKeysSettings,
            _indicesSettings)
        val _existingSettings: TableInfo = read(connection, "settings")
        if (!_infoSettings.equals(_existingSettings)) {
          return RoomOpenDelegate.ValidationResult(false, """
              |settings(com.marvel.reader.data.db.SettingEntity).
              | Expected:
              |""".trimMargin() + _infoSettings + """
              |
              | Found:
              |""".trimMargin() + _existingSettings)
        }
        return RoomOpenDelegate.ValidationResult(true, null)
      }
    }
    return _openDelegate
  }

  protected override fun createInvalidationTracker(): InvalidationTracker {
    val _shadowTablesMap: MutableMap<String, String> = mutableMapOf()
    val _viewTables: MutableMap<String, Set<String>> = mutableMapOf()
    return InvalidationTracker(this, _shadowTablesMap, _viewTables, "issues", "reading_progress",
        "reports", "settings")
  }

  public override fun clearAllTables() {
    super.performClear(false, "issues", "reading_progress", "reports", "settings")
  }

  protected override fun getRequiredTypeConverterClasses(): Map<KClass<*>, List<KClass<*>>> {
    val _typeConvertersMap: MutableMap<KClass<*>, List<KClass<*>>> = mutableMapOf()
    _typeConvertersMap.put(IssueDao::class, IssueDao_Impl.getRequiredConverters())
    _typeConvertersMap.put(ProgressDao::class, ProgressDao_Impl.getRequiredConverters())
    _typeConvertersMap.put(ReportDao::class, ReportDao_Impl.getRequiredConverters())
    _typeConvertersMap.put(SettingDao::class, SettingDao_Impl.getRequiredConverters())
    return _typeConvertersMap
  }

  public override fun getRequiredAutoMigrationSpecClasses(): Set<KClass<out AutoMigrationSpec>> {
    val _autoMigrationSpecsSet: MutableSet<KClass<out AutoMigrationSpec>> = mutableSetOf()
    return _autoMigrationSpecsSet
  }

  public override
      fun createAutoMigrations(autoMigrationSpecs: Map<KClass<out AutoMigrationSpec>, AutoMigrationSpec>):
      List<Migration> {
    val _autoMigrations: MutableList<Migration> = mutableListOf()
    return _autoMigrations
  }

  public override fun issueDao(): IssueDao = _issueDao.value

  public override fun progressDao(): ProgressDao = _progressDao.value

  public override fun reportDao(): ReportDao = _reportDao.value

  public override fun settingDao(): SettingDao = _settingDao.value
}
