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
import kotlin.Int
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
public class IssueDao_Impl(
  __db: RoomDatabase,
) : IssueDao {
  private val __db: RoomDatabase

  private val __upsertAdapterOfIssueEntity: EntityUpsertAdapter<IssueEntity>
  init {
    this.__db = __db
    this.__upsertAdapterOfIssueEntity = EntityUpsertAdapter<IssueEntity>(object :
        EntityInsertAdapter<IssueEntity>() {
      protected override fun createQuery(): String =
          "INSERT INTO `issues` (`orderNum`,`title`,`issue`,`phase`,`event`,`year`,`totalPages`,`availablePages`,`downloadedPages`) VALUES (?,?,?,?,?,?,?,?,?)"

      protected override fun bind(statement: SQLiteStatement, entity: IssueEntity) {
        statement.bindLong(1, entity.orderNum.toLong())
        statement.bindText(2, entity.title)
        statement.bindLong(3, entity.issue.toLong())
        statement.bindText(4, entity.phase)
        val _tmpEvent: String? = entity.event
        if (_tmpEvent == null) {
          statement.bindNull(5)
        } else {
          statement.bindText(5, _tmpEvent)
        }
        statement.bindText(6, entity.year)
        statement.bindLong(7, entity.totalPages.toLong())
        statement.bindLong(8, entity.availablePages.toLong())
        statement.bindLong(9, entity.downloadedPages.toLong())
      }
    }, object : EntityDeleteOrUpdateAdapter<IssueEntity>() {
      protected override fun createQuery(): String =
          "UPDATE `issues` SET `orderNum` = ?,`title` = ?,`issue` = ?,`phase` = ?,`event` = ?,`year` = ?,`totalPages` = ?,`availablePages` = ?,`downloadedPages` = ? WHERE `orderNum` = ?"

      protected override fun bind(statement: SQLiteStatement, entity: IssueEntity) {
        statement.bindLong(1, entity.orderNum.toLong())
        statement.bindText(2, entity.title)
        statement.bindLong(3, entity.issue.toLong())
        statement.bindText(4, entity.phase)
        val _tmpEvent: String? = entity.event
        if (_tmpEvent == null) {
          statement.bindNull(5)
        } else {
          statement.bindText(5, _tmpEvent)
        }
        statement.bindText(6, entity.year)
        statement.bindLong(7, entity.totalPages.toLong())
        statement.bindLong(8, entity.availablePages.toLong())
        statement.bindLong(9, entity.downloadedPages.toLong())
        statement.bindLong(10, entity.orderNum.toLong())
      }
    })
  }

  public override suspend fun upsertAll(issues: List<IssueEntity>): Unit = performSuspending(__db,
      false, true) { _connection ->
    __upsertAdapterOfIssueEntity.upsert(_connection, issues)
  }

  public override fun allFlow(): Flow<List<IssueEntity>> {
    val _sql: String = "SELECT * FROM issues ORDER BY orderNum ASC"
    return createFlow(__db, false, arrayOf("issues")) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        val _cursorIndexOfOrderNum: Int = getColumnIndexOrThrow(_stmt, "orderNum")
        val _cursorIndexOfTitle: Int = getColumnIndexOrThrow(_stmt, "title")
        val _cursorIndexOfIssue: Int = getColumnIndexOrThrow(_stmt, "issue")
        val _cursorIndexOfPhase: Int = getColumnIndexOrThrow(_stmt, "phase")
        val _cursorIndexOfEvent: Int = getColumnIndexOrThrow(_stmt, "event")
        val _cursorIndexOfYear: Int = getColumnIndexOrThrow(_stmt, "year")
        val _cursorIndexOfTotalPages: Int = getColumnIndexOrThrow(_stmt, "totalPages")
        val _cursorIndexOfAvailablePages: Int = getColumnIndexOrThrow(_stmt, "availablePages")
        val _cursorIndexOfDownloadedPages: Int = getColumnIndexOrThrow(_stmt, "downloadedPages")
        val _result: MutableList<IssueEntity> = mutableListOf()
        while (_stmt.step()) {
          val _item: IssueEntity
          val _tmpOrderNum: Int
          _tmpOrderNum = _stmt.getLong(_cursorIndexOfOrderNum).toInt()
          val _tmpTitle: String
          _tmpTitle = _stmt.getText(_cursorIndexOfTitle)
          val _tmpIssue: Int
          _tmpIssue = _stmt.getLong(_cursorIndexOfIssue).toInt()
          val _tmpPhase: String
          _tmpPhase = _stmt.getText(_cursorIndexOfPhase)
          val _tmpEvent: String?
          if (_stmt.isNull(_cursorIndexOfEvent)) {
            _tmpEvent = null
          } else {
            _tmpEvent = _stmt.getText(_cursorIndexOfEvent)
          }
          val _tmpYear: String
          _tmpYear = _stmt.getText(_cursorIndexOfYear)
          val _tmpTotalPages: Int
          _tmpTotalPages = _stmt.getLong(_cursorIndexOfTotalPages).toInt()
          val _tmpAvailablePages: Int
          _tmpAvailablePages = _stmt.getLong(_cursorIndexOfAvailablePages).toInt()
          val _tmpDownloadedPages: Int
          _tmpDownloadedPages = _stmt.getLong(_cursorIndexOfDownloadedPages).toInt()
          _item =
              IssueEntity(_tmpOrderNum,_tmpTitle,_tmpIssue,_tmpPhase,_tmpEvent,_tmpYear,_tmpTotalPages,_tmpAvailablePages,_tmpDownloadedPages)
          _result.add(_item)
        }
        _result
      } finally {
        _stmt.close()
      }
    }
  }

  public override suspend fun getAll(): List<IssueEntity> {
    val _sql: String = "SELECT * FROM issues ORDER BY orderNum ASC"
    return performSuspending(__db, true, false) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        val _cursorIndexOfOrderNum: Int = getColumnIndexOrThrow(_stmt, "orderNum")
        val _cursorIndexOfTitle: Int = getColumnIndexOrThrow(_stmt, "title")
        val _cursorIndexOfIssue: Int = getColumnIndexOrThrow(_stmt, "issue")
        val _cursorIndexOfPhase: Int = getColumnIndexOrThrow(_stmt, "phase")
        val _cursorIndexOfEvent: Int = getColumnIndexOrThrow(_stmt, "event")
        val _cursorIndexOfYear: Int = getColumnIndexOrThrow(_stmt, "year")
        val _cursorIndexOfTotalPages: Int = getColumnIndexOrThrow(_stmt, "totalPages")
        val _cursorIndexOfAvailablePages: Int = getColumnIndexOrThrow(_stmt, "availablePages")
        val _cursorIndexOfDownloadedPages: Int = getColumnIndexOrThrow(_stmt, "downloadedPages")
        val _result: MutableList<IssueEntity> = mutableListOf()
        while (_stmt.step()) {
          val _item: IssueEntity
          val _tmpOrderNum: Int
          _tmpOrderNum = _stmt.getLong(_cursorIndexOfOrderNum).toInt()
          val _tmpTitle: String
          _tmpTitle = _stmt.getText(_cursorIndexOfTitle)
          val _tmpIssue: Int
          _tmpIssue = _stmt.getLong(_cursorIndexOfIssue).toInt()
          val _tmpPhase: String
          _tmpPhase = _stmt.getText(_cursorIndexOfPhase)
          val _tmpEvent: String?
          if (_stmt.isNull(_cursorIndexOfEvent)) {
            _tmpEvent = null
          } else {
            _tmpEvent = _stmt.getText(_cursorIndexOfEvent)
          }
          val _tmpYear: String
          _tmpYear = _stmt.getText(_cursorIndexOfYear)
          val _tmpTotalPages: Int
          _tmpTotalPages = _stmt.getLong(_cursorIndexOfTotalPages).toInt()
          val _tmpAvailablePages: Int
          _tmpAvailablePages = _stmt.getLong(_cursorIndexOfAvailablePages).toInt()
          val _tmpDownloadedPages: Int
          _tmpDownloadedPages = _stmt.getLong(_cursorIndexOfDownloadedPages).toInt()
          _item =
              IssueEntity(_tmpOrderNum,_tmpTitle,_tmpIssue,_tmpPhase,_tmpEvent,_tmpYear,_tmpTotalPages,_tmpAvailablePages,_tmpDownloadedPages)
          _result.add(_item)
        }
        _result
      } finally {
        _stmt.close()
      }
    }
  }

  public override suspend fun getByOrder(orderNum: Int): IssueEntity? {
    val _sql: String = "SELECT * FROM issues WHERE orderNum = ?"
    return performSuspending(__db, true, false) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        var _argIndex: Int = 1
        _stmt.bindLong(_argIndex, orderNum.toLong())
        val _cursorIndexOfOrderNum: Int = getColumnIndexOrThrow(_stmt, "orderNum")
        val _cursorIndexOfTitle: Int = getColumnIndexOrThrow(_stmt, "title")
        val _cursorIndexOfIssue: Int = getColumnIndexOrThrow(_stmt, "issue")
        val _cursorIndexOfPhase: Int = getColumnIndexOrThrow(_stmt, "phase")
        val _cursorIndexOfEvent: Int = getColumnIndexOrThrow(_stmt, "event")
        val _cursorIndexOfYear: Int = getColumnIndexOrThrow(_stmt, "year")
        val _cursorIndexOfTotalPages: Int = getColumnIndexOrThrow(_stmt, "totalPages")
        val _cursorIndexOfAvailablePages: Int = getColumnIndexOrThrow(_stmt, "availablePages")
        val _cursorIndexOfDownloadedPages: Int = getColumnIndexOrThrow(_stmt, "downloadedPages")
        val _result: IssueEntity?
        if (_stmt.step()) {
          val _tmpOrderNum: Int
          _tmpOrderNum = _stmt.getLong(_cursorIndexOfOrderNum).toInt()
          val _tmpTitle: String
          _tmpTitle = _stmt.getText(_cursorIndexOfTitle)
          val _tmpIssue: Int
          _tmpIssue = _stmt.getLong(_cursorIndexOfIssue).toInt()
          val _tmpPhase: String
          _tmpPhase = _stmt.getText(_cursorIndexOfPhase)
          val _tmpEvent: String?
          if (_stmt.isNull(_cursorIndexOfEvent)) {
            _tmpEvent = null
          } else {
            _tmpEvent = _stmt.getText(_cursorIndexOfEvent)
          }
          val _tmpYear: String
          _tmpYear = _stmt.getText(_cursorIndexOfYear)
          val _tmpTotalPages: Int
          _tmpTotalPages = _stmt.getLong(_cursorIndexOfTotalPages).toInt()
          val _tmpAvailablePages: Int
          _tmpAvailablePages = _stmt.getLong(_cursorIndexOfAvailablePages).toInt()
          val _tmpDownloadedPages: Int
          _tmpDownloadedPages = _stmt.getLong(_cursorIndexOfDownloadedPages).toInt()
          _result =
              IssueEntity(_tmpOrderNum,_tmpTitle,_tmpIssue,_tmpPhase,_tmpEvent,_tmpYear,_tmpTotalPages,_tmpAvailablePages,_tmpDownloadedPages)
        } else {
          _result = null
        }
        _result
      } finally {
        _stmt.close()
      }
    }
  }

  public override suspend fun count(): Int {
    val _sql: String = "SELECT COUNT(*) FROM issues"
    return performSuspending(__db, true, false) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        val _result: Int
        if (_stmt.step()) {
          val _tmp: Int
          _tmp = _stmt.getLong(0).toInt()
          _result = _tmp
        } else {
          _result = 0
        }
        _result
      } finally {
        _stmt.close()
      }
    }
  }

  public override suspend fun updateDownloadedPages(orderNum: Int, count: Int) {
    val _sql: String = "UPDATE issues SET downloadedPages = ? WHERE orderNum = ?"
    return performSuspending(__db, false, true) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        var _argIndex: Int = 1
        _stmt.bindLong(_argIndex, count.toLong())
        _argIndex = 2
        _stmt.bindLong(_argIndex, orderNum.toLong())
        _stmt.step()
      } finally {
        _stmt.close()
      }
    }
  }

  public companion object {
    public fun getRequiredConverters(): List<KClass<*>> = emptyList()
  }
}
