package com.marvel.reader.data.db;

import android.database.Cursor;
import android.os.CancellationSignal;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.CoroutinesRoom;
import androidx.room.EntityDeletionOrUpdateAdapter;
import androidx.room.EntityInsertionAdapter;
import androidx.room.EntityUpsertionAdapter;
import androidx.room.RoomDatabase;
import androidx.room.RoomSQLiteQuery;
import androidx.room.SharedSQLiteStatement;
import androidx.room.util.CursorUtil;
import androidx.room.util.DBUtil;
import androidx.sqlite.db.SupportSQLiteStatement;
import java.lang.Class;
import java.lang.Exception;
import java.lang.Integer;
import java.lang.Object;
import java.lang.Override;
import java.lang.String;
import java.lang.SuppressWarnings;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Callable;
import javax.annotation.processing.Generated;
import kotlin.Unit;
import kotlin.coroutines.Continuation;
import kotlinx.coroutines.flow.Flow;

@Generated("androidx.room.RoomProcessor")
@SuppressWarnings({"unchecked", "deprecation"})
public final class IssueDao_Impl implements IssueDao {
  private final RoomDatabase __db;

  private final SharedSQLiteStatement __preparedStmtOfUpdateDownloadedPages;

  private final EntityUpsertionAdapter<IssueEntity> __upsertionAdapterOfIssueEntity;

  public IssueDao_Impl(@NonNull final RoomDatabase __db) {
    this.__db = __db;
    this.__preparedStmtOfUpdateDownloadedPages = new SharedSQLiteStatement(__db) {
      @Override
      @NonNull
      public String createQuery() {
        final String _query = "UPDATE issues SET downloadedPages = ? WHERE orderNum = ?";
        return _query;
      }
    };
    this.__upsertionAdapterOfIssueEntity = new EntityUpsertionAdapter<IssueEntity>(new EntityInsertionAdapter<IssueEntity>(__db) {
      @Override
      @NonNull
      protected String createQuery() {
        return "INSERT INTO `issues` (`orderNum`,`title`,`issue`,`phase`,`event`,`year`,`totalPages`,`availablePages`,`downloadedPages`) VALUES (?,?,?,?,?,?,?,?,?)";
      }

      @Override
      protected void bind(@NonNull final SupportSQLiteStatement statement,
          @NonNull final IssueEntity entity) {
        statement.bindLong(1, entity.getOrderNum());
        statement.bindString(2, entity.getTitle());
        statement.bindLong(3, entity.getIssue());
        statement.bindString(4, entity.getPhase());
        if (entity.getEvent() == null) {
          statement.bindNull(5);
        } else {
          statement.bindString(5, entity.getEvent());
        }
        statement.bindString(6, entity.getYear());
        statement.bindLong(7, entity.getTotalPages());
        statement.bindLong(8, entity.getAvailablePages());
        statement.bindLong(9, entity.getDownloadedPages());
      }
    }, new EntityDeletionOrUpdateAdapter<IssueEntity>(__db) {
      @Override
      @NonNull
      protected String createQuery() {
        return "UPDATE `issues` SET `orderNum` = ?,`title` = ?,`issue` = ?,`phase` = ?,`event` = ?,`year` = ?,`totalPages` = ?,`availablePages` = ?,`downloadedPages` = ? WHERE `orderNum` = ?";
      }

      @Override
      protected void bind(@NonNull final SupportSQLiteStatement statement,
          @NonNull final IssueEntity entity) {
        statement.bindLong(1, entity.getOrderNum());
        statement.bindString(2, entity.getTitle());
        statement.bindLong(3, entity.getIssue());
        statement.bindString(4, entity.getPhase());
        if (entity.getEvent() == null) {
          statement.bindNull(5);
        } else {
          statement.bindString(5, entity.getEvent());
        }
        statement.bindString(6, entity.getYear());
        statement.bindLong(7, entity.getTotalPages());
        statement.bindLong(8, entity.getAvailablePages());
        statement.bindLong(9, entity.getDownloadedPages());
        statement.bindLong(10, entity.getOrderNum());
      }
    });
  }

  @Override
  public Object updateDownloadedPages(final int orderNum, final int count,
      final Continuation<? super Unit> $completion) {
    return CoroutinesRoom.execute(__db, true, new Callable<Unit>() {
      @Override
      @NonNull
      public Unit call() throws Exception {
        final SupportSQLiteStatement _stmt = __preparedStmtOfUpdateDownloadedPages.acquire();
        int _argIndex = 1;
        _stmt.bindLong(_argIndex, count);
        _argIndex = 2;
        _stmt.bindLong(_argIndex, orderNum);
        try {
          __db.beginTransaction();
          try {
            _stmt.executeUpdateDelete();
            __db.setTransactionSuccessful();
            return Unit.INSTANCE;
          } finally {
            __db.endTransaction();
          }
        } finally {
          __preparedStmtOfUpdateDownloadedPages.release(_stmt);
        }
      }
    }, $completion);
  }

  @Override
  public Object upsertAll(final List<IssueEntity> issues,
      final Continuation<? super Unit> $completion) {
    return CoroutinesRoom.execute(__db, true, new Callable<Unit>() {
      @Override
      @NonNull
      public Unit call() throws Exception {
        __db.beginTransaction();
        try {
          __upsertionAdapterOfIssueEntity.upsert(issues);
          __db.setTransactionSuccessful();
          return Unit.INSTANCE;
        } finally {
          __db.endTransaction();
        }
      }
    }, $completion);
  }

  @Override
  public Flow<List<IssueEntity>> allFlow() {
    final String _sql = "SELECT * FROM issues ORDER BY orderNum ASC";
    final RoomSQLiteQuery _statement = RoomSQLiteQuery.acquire(_sql, 0);
    return CoroutinesRoom.createFlow(__db, false, new String[] {"issues"}, new Callable<List<IssueEntity>>() {
      @Override
      @NonNull
      public List<IssueEntity> call() throws Exception {
        final Cursor _cursor = DBUtil.query(__db, _statement, false, null);
        try {
          final int _cursorIndexOfOrderNum = CursorUtil.getColumnIndexOrThrow(_cursor, "orderNum");
          final int _cursorIndexOfTitle = CursorUtil.getColumnIndexOrThrow(_cursor, "title");
          final int _cursorIndexOfIssue = CursorUtil.getColumnIndexOrThrow(_cursor, "issue");
          final int _cursorIndexOfPhase = CursorUtil.getColumnIndexOrThrow(_cursor, "phase");
          final int _cursorIndexOfEvent = CursorUtil.getColumnIndexOrThrow(_cursor, "event");
          final int _cursorIndexOfYear = CursorUtil.getColumnIndexOrThrow(_cursor, "year");
          final int _cursorIndexOfTotalPages = CursorUtil.getColumnIndexOrThrow(_cursor, "totalPages");
          final int _cursorIndexOfAvailablePages = CursorUtil.getColumnIndexOrThrow(_cursor, "availablePages");
          final int _cursorIndexOfDownloadedPages = CursorUtil.getColumnIndexOrThrow(_cursor, "downloadedPages");
          final List<IssueEntity> _result = new ArrayList<IssueEntity>(_cursor.getCount());
          while (_cursor.moveToNext()) {
            final IssueEntity _item;
            final int _tmpOrderNum;
            _tmpOrderNum = _cursor.getInt(_cursorIndexOfOrderNum);
            final String _tmpTitle;
            _tmpTitle = _cursor.getString(_cursorIndexOfTitle);
            final int _tmpIssue;
            _tmpIssue = _cursor.getInt(_cursorIndexOfIssue);
            final String _tmpPhase;
            _tmpPhase = _cursor.getString(_cursorIndexOfPhase);
            final String _tmpEvent;
            if (_cursor.isNull(_cursorIndexOfEvent)) {
              _tmpEvent = null;
            } else {
              _tmpEvent = _cursor.getString(_cursorIndexOfEvent);
            }
            final String _tmpYear;
            _tmpYear = _cursor.getString(_cursorIndexOfYear);
            final int _tmpTotalPages;
            _tmpTotalPages = _cursor.getInt(_cursorIndexOfTotalPages);
            final int _tmpAvailablePages;
            _tmpAvailablePages = _cursor.getInt(_cursorIndexOfAvailablePages);
            final int _tmpDownloadedPages;
            _tmpDownloadedPages = _cursor.getInt(_cursorIndexOfDownloadedPages);
            _item = new IssueEntity(_tmpOrderNum,_tmpTitle,_tmpIssue,_tmpPhase,_tmpEvent,_tmpYear,_tmpTotalPages,_tmpAvailablePages,_tmpDownloadedPages);
            _result.add(_item);
          }
          return _result;
        } finally {
          _cursor.close();
        }
      }

      @Override
      protected void finalize() {
        _statement.release();
      }
    });
  }

  @Override
  public Object getAll(final Continuation<? super List<IssueEntity>> $completion) {
    final String _sql = "SELECT * FROM issues ORDER BY orderNum ASC";
    final RoomSQLiteQuery _statement = RoomSQLiteQuery.acquire(_sql, 0);
    final CancellationSignal _cancellationSignal = DBUtil.createCancellationSignal();
    return CoroutinesRoom.execute(__db, false, _cancellationSignal, new Callable<List<IssueEntity>>() {
      @Override
      @NonNull
      public List<IssueEntity> call() throws Exception {
        final Cursor _cursor = DBUtil.query(__db, _statement, false, null);
        try {
          final int _cursorIndexOfOrderNum = CursorUtil.getColumnIndexOrThrow(_cursor, "orderNum");
          final int _cursorIndexOfTitle = CursorUtil.getColumnIndexOrThrow(_cursor, "title");
          final int _cursorIndexOfIssue = CursorUtil.getColumnIndexOrThrow(_cursor, "issue");
          final int _cursorIndexOfPhase = CursorUtil.getColumnIndexOrThrow(_cursor, "phase");
          final int _cursorIndexOfEvent = CursorUtil.getColumnIndexOrThrow(_cursor, "event");
          final int _cursorIndexOfYear = CursorUtil.getColumnIndexOrThrow(_cursor, "year");
          final int _cursorIndexOfTotalPages = CursorUtil.getColumnIndexOrThrow(_cursor, "totalPages");
          final int _cursorIndexOfAvailablePages = CursorUtil.getColumnIndexOrThrow(_cursor, "availablePages");
          final int _cursorIndexOfDownloadedPages = CursorUtil.getColumnIndexOrThrow(_cursor, "downloadedPages");
          final List<IssueEntity> _result = new ArrayList<IssueEntity>(_cursor.getCount());
          while (_cursor.moveToNext()) {
            final IssueEntity _item;
            final int _tmpOrderNum;
            _tmpOrderNum = _cursor.getInt(_cursorIndexOfOrderNum);
            final String _tmpTitle;
            _tmpTitle = _cursor.getString(_cursorIndexOfTitle);
            final int _tmpIssue;
            _tmpIssue = _cursor.getInt(_cursorIndexOfIssue);
            final String _tmpPhase;
            _tmpPhase = _cursor.getString(_cursorIndexOfPhase);
            final String _tmpEvent;
            if (_cursor.isNull(_cursorIndexOfEvent)) {
              _tmpEvent = null;
            } else {
              _tmpEvent = _cursor.getString(_cursorIndexOfEvent);
            }
            final String _tmpYear;
            _tmpYear = _cursor.getString(_cursorIndexOfYear);
            final int _tmpTotalPages;
            _tmpTotalPages = _cursor.getInt(_cursorIndexOfTotalPages);
            final int _tmpAvailablePages;
            _tmpAvailablePages = _cursor.getInt(_cursorIndexOfAvailablePages);
            final int _tmpDownloadedPages;
            _tmpDownloadedPages = _cursor.getInt(_cursorIndexOfDownloadedPages);
            _item = new IssueEntity(_tmpOrderNum,_tmpTitle,_tmpIssue,_tmpPhase,_tmpEvent,_tmpYear,_tmpTotalPages,_tmpAvailablePages,_tmpDownloadedPages);
            _result.add(_item);
          }
          return _result;
        } finally {
          _cursor.close();
          _statement.release();
        }
      }
    }, $completion);
  }

  @Override
  public Object getByOrder(final int orderNum,
      final Continuation<? super IssueEntity> $completion) {
    final String _sql = "SELECT * FROM issues WHERE orderNum = ?";
    final RoomSQLiteQuery _statement = RoomSQLiteQuery.acquire(_sql, 1);
    int _argIndex = 1;
    _statement.bindLong(_argIndex, orderNum);
    final CancellationSignal _cancellationSignal = DBUtil.createCancellationSignal();
    return CoroutinesRoom.execute(__db, false, _cancellationSignal, new Callable<IssueEntity>() {
      @Override
      @Nullable
      public IssueEntity call() throws Exception {
        final Cursor _cursor = DBUtil.query(__db, _statement, false, null);
        try {
          final int _cursorIndexOfOrderNum = CursorUtil.getColumnIndexOrThrow(_cursor, "orderNum");
          final int _cursorIndexOfTitle = CursorUtil.getColumnIndexOrThrow(_cursor, "title");
          final int _cursorIndexOfIssue = CursorUtil.getColumnIndexOrThrow(_cursor, "issue");
          final int _cursorIndexOfPhase = CursorUtil.getColumnIndexOrThrow(_cursor, "phase");
          final int _cursorIndexOfEvent = CursorUtil.getColumnIndexOrThrow(_cursor, "event");
          final int _cursorIndexOfYear = CursorUtil.getColumnIndexOrThrow(_cursor, "year");
          final int _cursorIndexOfTotalPages = CursorUtil.getColumnIndexOrThrow(_cursor, "totalPages");
          final int _cursorIndexOfAvailablePages = CursorUtil.getColumnIndexOrThrow(_cursor, "availablePages");
          final int _cursorIndexOfDownloadedPages = CursorUtil.getColumnIndexOrThrow(_cursor, "downloadedPages");
          final IssueEntity _result;
          if (_cursor.moveToFirst()) {
            final int _tmpOrderNum;
            _tmpOrderNum = _cursor.getInt(_cursorIndexOfOrderNum);
            final String _tmpTitle;
            _tmpTitle = _cursor.getString(_cursorIndexOfTitle);
            final int _tmpIssue;
            _tmpIssue = _cursor.getInt(_cursorIndexOfIssue);
            final String _tmpPhase;
            _tmpPhase = _cursor.getString(_cursorIndexOfPhase);
            final String _tmpEvent;
            if (_cursor.isNull(_cursorIndexOfEvent)) {
              _tmpEvent = null;
            } else {
              _tmpEvent = _cursor.getString(_cursorIndexOfEvent);
            }
            final String _tmpYear;
            _tmpYear = _cursor.getString(_cursorIndexOfYear);
            final int _tmpTotalPages;
            _tmpTotalPages = _cursor.getInt(_cursorIndexOfTotalPages);
            final int _tmpAvailablePages;
            _tmpAvailablePages = _cursor.getInt(_cursorIndexOfAvailablePages);
            final int _tmpDownloadedPages;
            _tmpDownloadedPages = _cursor.getInt(_cursorIndexOfDownloadedPages);
            _result = new IssueEntity(_tmpOrderNum,_tmpTitle,_tmpIssue,_tmpPhase,_tmpEvent,_tmpYear,_tmpTotalPages,_tmpAvailablePages,_tmpDownloadedPages);
          } else {
            _result = null;
          }
          return _result;
        } finally {
          _cursor.close();
          _statement.release();
        }
      }
    }, $completion);
  }

  @Override
  public Object count(final Continuation<? super Integer> $completion) {
    final String _sql = "SELECT COUNT(*) FROM issues";
    final RoomSQLiteQuery _statement = RoomSQLiteQuery.acquire(_sql, 0);
    final CancellationSignal _cancellationSignal = DBUtil.createCancellationSignal();
    return CoroutinesRoom.execute(__db, false, _cancellationSignal, new Callable<Integer>() {
      @Override
      @NonNull
      public Integer call() throws Exception {
        final Cursor _cursor = DBUtil.query(__db, _statement, false, null);
        try {
          final Integer _result;
          if (_cursor.moveToFirst()) {
            final int _tmp;
            _tmp = _cursor.getInt(0);
            _result = _tmp;
          } else {
            _result = 0;
          }
          return _result;
        } finally {
          _cursor.close();
          _statement.release();
        }
      }
    }, $completion);
  }

  @NonNull
  public static List<Class<?>> getRequiredConverters() {
    return Collections.emptyList();
  }
}
