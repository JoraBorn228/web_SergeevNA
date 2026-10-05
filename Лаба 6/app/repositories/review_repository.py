from app.models import Review, Course
from datetime import datetime
from typing import Optional


class ReviewRepository:
    def __init__(self, db):
        self.db = db

    def get_by_course_and_user(self, course_id: int, user_id: int) -> Optional[Review]:
        return self.db.session.execute(
            self.db.select(Review).filter_by(course_id=course_id, user_id=user_id)
        ).scalar()

    def get_last_five(self, course_id: int):
        return self.db.session.execute(
            self.db.select(Review)
            .filter_by(course_id=course_id)
            .order_by(Review.created_at.desc())
            .limit(5)
        ).scalars().all()

    def get_pagination_info(self, course_id: int, sort_order: str, page: int):
        query = self.db.select(Review).filter_by(course_id=course_id)

        if sort_order == 'positive':
            query = query.order_by(Review.rating.desc(), Review.created_at.desc(), Review.id.desc())
        elif sort_order == 'negative':
            query = query.order_by(Review.rating.asc(), Review.created_at.desc(), Review.id.desc())
        else:
            query = query.order_by(Review.created_at.desc(), Review.id.desc())

        return self.db.paginate(query, page=page, per_page=10)

    def create(self, rating: int, text: str, course_id: int, user_id: int):
        review = Review(
            rating=rating,
            text=text,
            course_id=course_id,
            user_id=user_id,
            created_at=datetime.now()
        )
        self.db.session.add(review)
        course = self.db.session.get(Course, course_id)
        if course is not None:
            course.rating_sum += rating
            course.rating_num += 1
        self.db.session.commit()
        return review

    def update(self, review: Review, rating: int, text: str):
        review.rating = rating
        review.text = text
        self.db.session.commit()
        return review
