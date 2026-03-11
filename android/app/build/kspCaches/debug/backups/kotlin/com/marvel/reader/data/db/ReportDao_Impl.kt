package com.marvel.reader.`data`.db

import androidx.room.EntityDeleteOrUpdateAdapter
import androidx.room.EntityInsertAdapter
import androidx.room.EntityUpsertAdapter
import androidx.room.RoomDatabase
import androidx.room.coroutines.createFlow
import androidx.room.util.getColumnIndexOrThrow
import androidx.room.util.performSuspending
import androidx.sqlite.SQLiteStatement
import javax.`annotation`.processing.Generated
import kotlin.Boolean
import kotlin.Int
import kotlin.Long
import kotlin.String
import kotlin.Suppress
import kotlin.Unit
import kotlin.collections.List
import kotlin.collections.MutableList
import kotlin.collections.mutableListOf
import kotlin.reflect.KClass
import kotlinx.coroutines.flow.Flow

@Generated(value = ["androidx.room.RoomProcessor"])
@Suppress(names = ["UNCHECKED_CAST", "DEPRECATION", "REDUNDANT_PROJECTION", "REMOVAL"])
public class ReportDao_Impl(
  __db: RoomDatabase,
) : ReportDao {
  private val __db: RoomDatabase

  private val __insertAdapterOfReportEntity: EntityInsertAdapter<ReportEntity>

  private val __upsertAdapterOfReportEntity: EntityUpsertAdapter<ReportEntity>
  init {
    this.__db = __db
    this.__insertAdapterOfReportEntity = object : EntityInsertAdapter<ReportEntity>() {
      protected override fun createQuery(): String =
          "INSERT OR ABORT INTO `reports` (`id`,`issueOrder`,`pageNum`,`reportType`,`description`,`resolved`,`createdAt`) VALUES (nullif(?, 0),?,?,?,?,?,?)"

      protected override fun bind(statement: SQLiteStatement, entity: ReportEntity) {
        statement.bindLong(1, entity.id.toLong())
        statement.bindLong(2, entity.issueOrder.toLong())
        val _tmpPageNum: Int? = entity.pageNum
        if (_tmpPageNum == null) {
          statement.bindNull(3)
        } else {
          statement.bindLong(3, _tmpPageNum.toLong())
        }
        statement.bindText(4, entity.reportType)
        statement.bindText(5, entity.description)
        val _tmp: Int = if (entity.resolved) 1 else 0
        statement.bindLong(6, _tmp.toLong())
        statement.bindText(7, entity.createdAt)
      }
    }
    this.__upsertAdapterOfReportEntity = EntityUpsertAdapter<ReportEntity>(object :
        EntityInsertAdapter<ReportEntity>() {
      protected override fun createQuery(): String =
          "INSERT INTO `reports` (`id`,`issueOrder`,`pageNum`,`reportType`,`description`,`resolved`,`createdAt`) VALUES (nullif(?, 0),?,?,?,?,?,?)"

      protected override fun bind(statement: SQLiteStatement, entity: ReportEntity) {
        statement.bindLong(1, entity.id.toLong())
        statement.bindLong(2, entity.issueOrder.toLong())
        val _tmpPageNum: Int? = entity.pageNum
        if (_tmpPageNum == null) {
          statement.bindNull(3)
        } else {
          statement.bindLong(3, _tmpPageNum.toLong())
        }
        statement.bindText(4, entity.reportType)
        statement.bindText(5, entity.description)
        val _tmp: Int = if (entity.resolved) 1 else 0
        statement.bindLong(6, _tmp.toLong())
        statement.bindText(7, entity.createdAt)
      }
    }, object : EntityDeleteOrUpdateAdapter<ReportEntity>() {
      protected override fun createQuery(): String =
          "UPDATE `reports` SET `id` = ?,`issueOrder` = ?,`pageNum` = ?,`reportType` = ?,`description` = ?,`resolved` = ?,`createdAt` = ? WHERE `id` = ?"

      protected override fun bind(statement: SQLiteStatement, entity: ReportEntity) {
        statement.bindLong(1, entity.id.toLong())
        statement.bindLong(2, entity.issueOrder.toLong())
        val _tmpPageNum: Int? = entity.pageNum
        if (_tmpPageNum == null) {
          statement.bindNull(3)
        } else {
          statement.bindLong(3, _tmpPageNum.toLong())
        }
        statement.bindText(4, entity.reportType)
        statement.bindText(5, entity.description)
        val _tmp: Int = if (entity.resolved) 1 else 0
        statement.bindLong(6, _tmp.toLong())
        statement.bindText(7, entity.createdAt)
        statement.bindLong(8, entity.id.toLong())
      }
    })
  }

  public override suspend fun insert(report: ReportEntity): Long = performSuspending(__db, false,
      true) { _connection ->
    val _result: Long = __insertAdapterOfReportEntity.insertAndReturnId(_connection, report)
    _result
  }

  public override suspend fun upsertAll(reports: List<ReportEntity>): Unit = performSuspending(__db,
      false, true) { _connection ->
    __upsertAdapterOfReportEntity.upsert(_connection, reports)
  }

  public override suspend fun getUnresolved(): List<ReportEntity> {
    val _sql: String = "SELECT * FROM reports WHERE resolved = 0 ORDER BY id DESC"
    return performSuspending(__db, true, false) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        val _cursorIndexOfId: Int = getColumnIndexOrThrow(_stmt, "id")
        val _cursorIndexOfIssueOrder: Int = getColumnIndexOrThrow(_stmt, "issueOrder")
        val _cursorIndexOfPageNum: Int = getColumnIndexOrThrow(_stmt, "pageNum")
        val _cursorIndexOfReportType: Int = getColumnIndexOrThrow(_stmt, "reportType")
        val _cursorIndexOfDescription: Int = getColumnIndexOrThrow(_stmt, "description")
        val _cursorIndexOfResolved: Int = getColumnIndexOrThrow(_stmt, "resolved")
        val _cursorIndexOfCreatedAt: Int = getColumnIndexOrThrow(_stmt, "createdAt")
        val _result: MutableList<ReportEntity> = mutableListOf()
        while (_stmt.step()) {
          val _item: ReportEntity
          val _tmpId: Int
          _tmpId = _stmt.getLong(_cursorIndexOfId).toInt()
          val _tmpIssueOrder: Int
          _tmpIssueOrder = _stmt.getLong(_cursorIndexOfIssueOrder).toInt()
          val _tmpPageNum: Int?
          if (_stmt.isNull(_cursorIndexOfPageNum)) {
            _tmpPageNum = null
          } else {
            _tmpPageNum = _stmt.getLong(_cursorIndexOfPageNum).toInt()
          }
          val _tmpReportType: String
          _tmpReportType = _stmt.getText(_cursorIndexOfReportType)
          val _tmpDescription: String
          _tmpDescription = _stmt.getText(_cursorIndexOfDescription)
          val _tmpResolved: Boolean
          val _tmp: Int
          _tmp = _stmt.getLong(_cursorIndexOfResolved).toInt()
          _tmpResolved = _tmp != 0
          val _tmpCreatedAt: String
          _tmpCreatedAt = _stmt.getText(_cursorIndexOfCreatedAt)
          _item =
              ReportEntity(_tmpId,_tmpIssueOrder,_tmpPageNum,_tmpReportType,_tmpDescription,_tmpResolved,_tmpCreatedAt)
          _result.add(_item)
        }
        _result
      } finally {
        _stmt.close()
      }
    }
  }

  public override fun flaggedFlow(): Flow<List<Int>> {
    val _sql: String = "SELECT DISTINCT issueOrder FROM reports WHERE resolved = 0"
    return createFlow(__db, false, arrayOf("reports")) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        val _result: MutableList<Int> = mutableListOf()
        while (_stmt.step()) {
          val _item: Int
          _item = _stmt.getLong(0).toInt()
          _result.add(_item)
        }
        _result
      } finally {
        _stmt.close()
      }
    }
  }

  public companion object {
    public fun getRequiredConverters(): List<KClass<*>> = emptyList()
  }
}
