import time

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from RecordPool import RecordPool
from utils import Site

import os, os.path
import uuid


class BPMSupreme(RecordPool):
    def __init__(self):
        super().__init__(Site.BPMSUPREME)
        self.url = "https://app.bpmsupreme.com/new-releases/classic/audio"
        self.wait_time = 10
        self.track_ignore = (
            "Short Edit",
            "Clean Short Edit",
            "Dirty Short Edit",
            "Quick Hit Clean",
            "Quick Hit",
            "Quick Hit Dirty",
        )

        self.genre_ignore = (
            "Alternative",
            "Bachata",
            "Banda",
            "Country",
            "Corrido",
            "Cumbia",
            "Cumbias",
            "Dancehall",
            "Dembow",
            "Drum Loops",
            "Latin Pop",
            "Mambo",
            "Mariachi",
            "Norteno",
            "Reggae",
            "Reggaeton",
            "Rock",
            "Salsa",
            "Scratch Tools",
            "Soca",
        )

    def click(self, element):
        self.driver.execute_script("arguments[0].click()", element)

    def close_error_popup(self):
        elements = self.driver.find_elements(By.XPATH, ".//*[@class='sweet-alert showSweetAlert visible']")
        if elements:
            button = elements[0].find_element_by_class_name("confirm")
            self.click(button)
            time.sleep(0.5)

    def download(self, track):
        try:
            self.click(track)
            # give download a bit of time to start before returning
            time.sleep(0.6)
        except StaleElementReferenceException:
            return

    def get_page_number(self) -> int:
        WebDriverWait(self.driver, self.wait_time).until(
            expected_conditions.visibility_of_element_located((By.CLASS_NAME, "paging_paging__container--left__06CUU"))
        )
        container = self.driver.find_element(By.CLASS_NAME, "paging_paging__container--left__06CUU")
        parent = container.find_element(By.CLASS_NAME, "dropdown_dropdown__labels-container__B2ZiN")
        page = parent.find_elements(By.TAG_NAME, "div")[0]
        number = int(page.text)
        return number

    def get_track_version_element_list(self, song_row_element):
        accordion_button = song_row_element.find_element(By.CLASS_NAME, "accordion-count-column_accordion-count-column__accordion-button__U0mpI")
        self.click(accordion_button)
        # give time for accordion to open
        try:
            WebDriverWait(self.driver, self.wait_time).until(
                expected_conditions.visibility_of_element_located((By.XPATH, ".//*[@class='download-accordion_download-accordion__container__Nmr2W' and @style='height: auto;']"))
            )
        except TimeoutException:
            print(f"Failed to open accordion for song")
            return -1

        track_versions_container = song_row_element.find_element(By.XPATH, "./*[@class='download-accordion_download-accordion__container__Nmr2W' and @style='height: auto;']")
        track_versions_list = track_versions_container.find_elements(By.XPATH, "./*[@class='download-accordion_download-accordion__item__zSAJc']")
        return track_versions_list

    def get_num_downloads_so_far(self, track_version_element):
        download_links_column = track_version_element.find_element(By.CLASS_NAME, "download-accordion_download-accordion__column--versions-content__W_eAZ")

        possible_download_num_text_element = download_links_column.find_elements(By.CLASS_NAME, "download-accordion_download-accordion__download-btn-text__k_qSj")
        if len(possible_download_num_text_element) < 1:
          return -1
        download_num_text = possible_download_num_text_element[0].text
        download_num_string = download_num_text.split()[0]
        download_int = int(download_num_string)
        return download_int

    def click_download_link_for_version(self, track_version_element):
        download_links_column = track_version_element.find_element(By.CLASS_NAME, "download-accordion_download-accordion__column--versions-content__W_eAZ")
        download_link = download_links_column.find_element(By.CLASS_NAME, "download-accordion_download-accordion__download-btn__sjMJQ")
        print('clicking link')
        self.click(download_link)

    def get_num_files_in_directory(self, dir):
        return len([name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))])

    def get_tracks(self, number=0) -> list:
        tracks = []
        try:
            # wait for songs to load
            WebDriverWait(self.driver, self.wait_time).until(
                expected_conditions.visibility_of_element_located((By.CLASS_NAME, "track-list-supreme_track-list__PamRB"))
            )
        except TimeoutException:
            print(f"No tracks found after waiting for {self.wait_time} seconds...")
            return tracks

        playlist = self.driver.find_element(By.CLASS_NAME, "track-list-supreme_track-list__PamRB")
        songs = playlist.find_elements(By.XPATH, "./*[@draggable='true']")
        print(f"Num songs = {len(songs)}")
        num_max = min(number, len(songs)) if number > 0 else len(songs)
        failures_in_a_row = 0
        for song in songs[:num_max]:
            #genre = song.find_element_by_xpath(".//*[@class='col-category link']")
            #if genre.text in self.genre_ignore:
            #    continue
            track_version_element_list = self.get_track_version_element_list(song)

            #DIR = '/Users/alex/Desktop/DJ MUSIC SORT/BPMSUPREME/'
            DIR = '/Volumes/SANDISK5/DJ MUSIC SORT/BPMSUPREME'
            pre_num_files_in_directory = self.get_num_files_in_directory(DIR)

            downloaded_something = False
            num_downloads=0
            for track_version_element in track_version_element_list:
                downloads_so_far = self.get_num_downloads_so_far(track_version_element)
                print(f'downloads_so_far={downloads_so_far}')
                if downloads_so_far == 0:
                    self.click_download_link_for_version(track_version_element)
                    num_downloads += 1
                    # sleep so the download doesn't skip
                    time.sleep(1.5)
                    downloaded_something = True

            expected_num_files_in_directory = pre_num_files_in_directory + num_downloads
            post_num_files_in_directory = self.get_num_files_in_directory(DIR)

            print(f'num_downloads = {num_downloads}')
            print(f'pre_num_files_in_directory = {pre_num_files_in_directory}')
            print(f'post_num_files_in_directory = {post_num_files_in_directory}')
            print(f'expected_num_files_in_directory = {expected_num_files_in_directory}')

            retry_count=0
            while post_num_files_in_directory < expected_num_files_in_directory and retry_count < 40:
              print(f'retrying, retry_count={retry_count}')
              time.sleep(0.25)
              post_num_files_in_directory = self.get_num_files_in_directory(DIR)
              retry_count += 1

            if retry_count > 0:
              print(f'num_downloads = {num_downloads}')
              print(f'pre_num_files_in_directory = {pre_num_files_in_directory}')
              print(f'post_num_files_in_directory = {post_num_files_in_directory}')
              print(f'expected_num_files_in_directory = {expected_num_files_in_directory}')

            if post_num_files_in_directory < expected_num_files_in_directory:
              screenshot_path = os.path.join(DIR, "errors", f"{str(uuid.uuid4())}.png")
              song.screenshot(screenshot_path)
              print(f"Error: Expected more downloads than we received in our file system. Screenshot saved in {screenshot_path}. Double check")
              #input("Press enter to continue anyway: ")
              failures_in_a_row += 1
            else:
              failures_in_a_row = 0

            if failures_in_a_row >= 4:
              print(f"Note: had 4 errors in a row. Please check error screenshots and check functionality before continuing")
              input("Press enter to continue: ")

            if downloaded_something:
              pass
              #input("Press enter to continue\n")


            #tag = song.find_element_by_class_name("row-tags")
            #elements = tag.find_elements_by_xpath(".//*[@class='tag-view ']")
            #filtered = [e for e in elements if e.text not in self.track_ignore]
            #if filtered:
            #    tracks.extend(filtered)

        #return tracks
        return []

    def next_page(self) -> bool:
        self.close_error_popup()
        if self.driver.current_url != self.current_url:
            self.reload_page()

        try:
            container = self.driver.find_element(By.CLASS_NAME, "paging_paging__next-btn__0IX8t")
            #element = container.find_element_by_xpath("//*[contains(text(), '›')]")
            is_disabled = container.get_attribute('disabled')
            print(f'is_disabled = {is_disabled}')
            if is_disabled:
              return False
            else:
              self.click(container)
        except (
            ElementNotInteractableException,
            ElementClickInterceptedException,
            TimeoutException,
        ):
            return False

        self.update_current_page()
        return True

    def prepare_pool(self):
        input("Choose genres manually and press a key to continue...")
