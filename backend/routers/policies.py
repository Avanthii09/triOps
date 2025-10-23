from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from database.database import get_db
from database.models import Policy
from schemas import PolicySearchRequest, Policy as PolicySchema

router = APIRouter()

@router.get("/cancellation-policy")
async def get_cancellation_policy(db: Session = Depends(get_db)):
    """Get airline cancellation policy details"""
    try:
        policy = db.query(Policy).filter(
            and_(Policy.policy_type == "cancellation", Policy.is_active == True)
        ).order_by(Policy.effective_date.desc()).first()
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cancellation policy not found"
            )
        
        return {
            "policy_type": policy.policy_type,
            "title": policy.title,
            "content": policy.content,
            "effective_date": policy.effective_date.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving cancellation policy: {str(e)}"
        )

@router.get("/pet-travel-policy")
async def get_pet_travel_policy(db: Session = Depends(get_db)):
    """Get pet travel policy details"""
    try:
        policy = db.query(Policy).filter(
            and_(Policy.policy_type == "pet_travel", Policy.is_active == True)
        ).order_by(Policy.effective_date.desc()).first()
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pet travel policy not found"
            )
        
        return {
            "policy_type": policy.policy_type,
            "title": policy.title,
            "content": policy.content,
            "effective_date": policy.effective_date.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving pet travel policy: {str(e)}"
        )

@router.post("/search")
async def search_policies(
    search_request: PolicySearchRequest,
    db: Session = Depends(get_db)
):
    """Search for policies by keyword or type"""
    try:
        query = db.query(Policy).filter(Policy.is_active == True)
        
        # Add search term filter
        search_filter = or_(
            Policy.title.ilike(f"%{search_request.search_term}%"),
            Policy.content.ilike(f"%{search_request.search_term}%")
        )
        query = query.filter(search_filter)
        
        # Add policy type filter if provided
        if search_request.policy_type:
            query = query.filter(Policy.policy_type == search_request.policy_type)
        
        policies = query.order_by(Policy.effective_date.desc()).all()
        
        if not policies:
            return {
                "message": f"No policies found matching '{search_request.search_term}'",
                "policies": []
            }
        
        policy_list = [
            {
                "policy_id": str(policy.policy_id),
                "policy_type": policy.policy_type,
                "title": policy.title,
                "content": policy.content[:200] + "..." if len(policy.content) > 200 else policy.content,
                "effective_date": policy.effective_date.isoformat()
            }
            for policy in policies
        ]
        
        return {
            "search_term": search_request.search_term,
            "policies": policy_list,
            "total_found": len(policy_list)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching policies: {str(e)}"
        )

@router.get("/all")
async def get_all_policies(
    policy_type: str = None,
    db: Session = Depends(get_db)
):
    """Get all active policies"""
    try:
        query = db.query(Policy).filter(Policy.is_active == True)
        
        if policy_type:
            query = query.filter(Policy.policy_type == policy_type)
        
        policies = query.order_by(Policy.policy_type, Policy.effective_date.desc()).all()
        
        if not policies:
            return {
                "message": "No active policies found",
                "policies": []
            }
        
        # Group policies by type
        grouped_policies = {}
        for policy in policies:
            if policy.policy_type not in grouped_policies:
                grouped_policies[policy.policy_type] = []
            grouped_policies[policy.policy_type].append({
                "policy_id": str(policy.policy_id),
                "title": policy.title,
                "content": policy.content,
                "effective_date": policy.effective_date.isoformat()
            })
        
        return {
            "policies_by_type": grouped_policies,
            "total_policies": len(policies)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving policies: {str(e)}"
        )

@router.get("/types")
async def get_policy_types(db: Session = Depends(get_db)):
    """Get all available policy types"""
    try:
        policy_types = db.query(Policy.policy_type).filter(
            Policy.is_active == True
        ).distinct().all()
        
        return {
            "policy_types": [pt[0] for pt in policy_types]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving policy types: {str(e)}"
        )
