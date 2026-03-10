package com.marvel.reader

import android.app.Application
import com.marvel.reader.data.api.SyncApi
import com.marvel.reader.data.db.AppDatabase
import com.marvel.reader.data.repository.ComicRepository
import com.marvel.reader.data.storage.ImageStorage

class MarvelReaderApp : Application() {
    val database by lazy { AppDatabase.getInstance(this) }
    val imageStorage by lazy { ImageStorage(this) }
    val syncApi by lazy { SyncApi() }
    val repository by lazy { ComicRepository(database, syncApi, imageStorage) }
}
